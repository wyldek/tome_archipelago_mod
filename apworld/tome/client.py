"""Archipelago 0.6.7 CommonClient bridge for Tales of Maj'Eyal."""
from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
import time

import Utils
from CommonClient import (
    CommonContext,
    ClientCommandProcessor,
    get_base_parser,
    handle_url_arg,
    server_loop,
)
from NetUtils import ClientStatus

from .core.model import Identity, Receipt, ValidationError
from .bridge_mailbox import (
    atomic_write_json,
    client_snapshot,
    exclusive_bridge,
    read_json,
    validate_contract,
    validate_game_snapshot,
)

LOG = logging.getLogger("ToMEArchipelago")
PERSIST_CATEGORY = "tome_archipelago"
PERSIST_MAILBOX_KEY = "mailbox"


def _shop_location_codes(contract: dict) -> list[int]:
    return sorted(loc["code"] for loc in contract.get("locations", []) if loc.get("event") == "shop")


def _scout_snapshot(ctx) -> list[dict]:
    """Resolve exact item/recipient metadata for paid shop checks."""
    if not ctx.contract:
        return []
    out = []
    for code in _shop_location_codes(ctx.contract):
        info = ctx.locations_info.get(code)
        if not info:
            continue
        try:
            item_name = ctx.item_names.lookup_in_slot(info.item, info.player)
        except Exception:
            # The addon intentionally shows no generic parcel fallback. A shop
            # check appears only after its exact AP item name can be resolved.
            continue
        player_name = ctx.player_names.get(info.player, f"Player {info.player}")
        out.append({
            "location": code,
            "item": info.item,
            "item_name": item_name,
            "player": info.player,
            "player_name": player_name,
            "flags": info.flags,
        })
    return out


def _resolve_mailbox(value: str | None) -> Path:
    if value:
        path = Path(value).expanduser().resolve()
        Utils.persistent_store(PERSIST_CATEGORY, PERSIST_MAILBOX_KEY, str(path))
        return path

    cached = Utils.persistent_load().get(PERSIST_CATEGORY, {}).get(PERSIST_MAILBOX_KEY)
    if cached:
        return Path(cached).expanduser().resolve()

    print("Tales of Maj'Eyal Archipelago needs the addon mailbox directory.")
    print(r"Example: C:\Users\you\T-Engine\4.0\tome\archipelago")
    entered = input("Mailbox directory: ").strip().strip('"')
    if not entered:
        raise SystemExit("A mailbox directory is required.")
    path = Path(entered).expanduser().resolve()
    Utils.persistent_store(PERSIST_CATEGORY, PERSIST_MAILBOX_KEY, str(path))
    return path


class ToMECommands(ClientCommandProcessor):
    def _cmd_tome(self):
        self.output(
            f"Mailbox: {self.ctx.mailbox}; binding: {self.ctx.identity}; "
            f"error: {self.ctx.last_error or 'none'}"
        )

    async def _cmd_resync(self):
        await self.ctx.send_msgs([
            {"cmd": "Sync"},
            {"cmd": "LocationChecks", "locations": sorted(self.ctx.pending_checks)},
        ])


class ToMEContext(CommonContext):
    game = "Tales of Maj'Eyal"
    items_handling = 0b111
    command_processor = ToMECommands

    def __init__(self, server, password, mailbox: Path, name: str | None):
        super().__init__(server, password)
        self.auth = name
        self.mailbox = mailbox
        self.identity = None
        self.contract = None
        self.room_seed = None
        self.pending_checks = set()
        self.revision = 0
        self.last_error = None
        self.dirty = True
        self.last_publish = 0.0
        self.history_ready = False
        self.goal_sent = False
        self.last_snapshot = None
        self.persisted_checks = None

    async def server_auth(self, password_requested=False):
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        if not self.auth:
            await self.get_username()
        await self.send_connect()

    async def connection_closed(self):
        await super().connection_closed()
        self.history_ready = False
        if self.last_snapshot:
            self.last_snapshot["connected"] = False
            atomic_write_json(self.mailbox / "client.json", self.last_snapshot)

    def on_package(self, cmd, args):
        # CommonClient processes its state before this hook.
        if cmd == "RoomInfo":
            self.room_seed = args["seed_name"]
        elif cmd == "Connected":
            self.contract = validate_contract(args["slot_data"])
            self.identity = Identity(
                self.room_seed or self.seed_name,
                args["team"],
                args["slot"],
                self.contract["contract_hash"],
            )
            self.history_ready = False
            self.persisted_checks = None
            self.goal_sent = False
            cached = read_json(self.mailbox / "bridge-state.json")
            if cached and cached.get("identity") == self.identity.to_dict():
                self.pending_checks = set(cached.get("checks", []))
            else:
                self.pending_checks = set()
            self.dirty = True
            msgs = [{"cmd": "Sync"}]
            shop_codes = [
                code for code in _shop_location_codes(self.contract)
                if code in self.server_locations
            ]
            if shop_codes:
                msgs.append({
                    "cmd": "LocationScouts",
                    "locations": shop_codes,
                    "create_as_hint": 0,
                })
            asyncio.create_task(self.send_msgs(msgs))
        elif cmd == "ReceivedItems":
            if args["index"] == 0:
                self.history_ready = True
            self.dirty = True
        elif cmd in {"LocationInfo", "RoomUpdate"}:
            self.dirty = True


async def _watcher(ctx: ToMEContext):
    last_send = 0.0
    while not ctx.exit_event.is_set():
        try:
            connected = bool(ctx.server and ctx.slot is not None)
            if ctx.identity and ctx.contract and ctx.history_ready:
                active = {loc["code"] for loc in ctx.contract["locations"]}
                if ctx.dirty or time.monotonic() - ctx.last_publish > 2:
                    receipts = [Receipt(i.item, i.location, i.player, i.flags) for i in ctx.items_received]
                    ctx.revision += 1
                    snapshot = client_snapshot(
                        ctx.identity,
                        ctx.contract,
                        receipts,
                        set(ctx.checked_locations),
                        ctx.revision,
                        connected,
                        _scout_snapshot(ctx),
                    )
                    atomic_write_json(ctx.mailbox / "client.json", snapshot)
                    ctx.last_snapshot = snapshot
                    ctx.last_publish = time.monotonic()
                    ctx.dirty = False

                game = read_json(ctx.mailbox / "game.json")
                if game:
                    validate_game_snapshot(game, ctx.identity, active)
                    if game["applied_count"] > len(ctx.items_received):
                        raise ValidationError("ToME save is ahead of AP item history; refusing sync")
                    if game.get("error"):
                        raise ValidationError("ToME grant error: " + str(game["error"]))
                    ctx.pending_checks.update(game["checks"])
                    ctx.pending_checks.intersection_update(active)
                    if ctx.persisted_checks != ctx.pending_checks:
                        atomic_write_json(
                            ctx.mailbox / "bridge-state.json",
                            {"identity": ctx.identity.to_dict(), "checks": sorted(ctx.pending_checks)},
                        )
                        ctx.persisted_checks = set(ctx.pending_checks)
                    unsent = ctx.pending_checks - set(ctx.checked_locations)
                    if connected and unsent and time.monotonic() - last_send > 1:
                        await ctx.send_msgs([{"cmd": "LocationChecks", "locations": sorted(unsent)}])
                        last_send = time.monotonic()
                    if connected and game["goal"] and not ctx.goal_sent:
                        await ctx.send_msgs([
                            {"cmd": "LocationChecks", "locations": sorted(ctx.pending_checks)},
                            {"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL},
                        ])
                        ctx.goal_sent = True
                ctx.last_error = None
        except (ValidationError, KeyError, TypeError, OSError) as exc:
            message = str(exc)
            if ctx.last_error != message:
                LOG.error("Sync paused: %s", message)
                ctx.last_error = message
        await asyncio.sleep(0.25)


async def _run(args) -> None:
    mailbox = _resolve_mailbox(args.mailbox)
    ctx = ToMEContext(args.connect, args.password, mailbox, args.name)
    ctx.mailbox.mkdir(parents=True, exist_ok=True)
    with exclusive_bridge(ctx.mailbox / "bridge.lock"):
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="AP server")
        ctx.run_cli()
        task = asyncio.create_task(_watcher(ctx), name="ToME mailbox")
        try:
            await ctx.exit_event.wait()
        finally:
            ctx.server_address = None
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            if ctx.last_snapshot:
                ctx.last_snapshot["connected"] = False
                atomic_write_json(ctx.mailbox / "client.json", ctx.last_snapshot)
            await ctx.shutdown()


def launch_tome_client(*argv: str) -> None:
    Utils.init_logging("ToMEClient", exception_logger="Client")
    parser = get_base_parser(description="Tales of Maj'Eyal Archipelago bridge")
    parser.add_argument("--name", default=None, help="Archipelago slot name.")
    parser.add_argument("--mailbox", default=None, help="ToME addon mailbox directory; remembered after first use.")
    parser.add_argument("url", nargs="?", help="archipelago:// connection URL from the Launcher/WebHost")
    args = parser.parse_args(argv)
    args = handle_url_arg(args, parser=parser)
    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    launch_tome_client()
