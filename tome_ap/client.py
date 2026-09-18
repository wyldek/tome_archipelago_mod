"""Standalone/launcher-compatible Archipelago bridge for Tales of Maj'Eyal.

The preferred path is the client embedded in tome.apworld.  This fallback can
run directly against an Archipelago source checkout, or delegate to an installed
ArchipelagoLauncher when using the normal frozen Windows distribution.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from .model import Identity, Receipt, ValidationError
from .mailbox import (
    atomic_write_json,
    client_snapshot,
    read_json,
    validate_contract,
    validate_game_snapshot,
    exclusive_bridge,
)

LOG = logging.getLogger("ToMEArchipelago")
PERSIST_CATEGORY = "tome_archipelago"
PERSIST_MAILBOX_KEY = "mailbox"
MAILBOX_MARKER_NAME = "mailbox-info.json"
MAILBOX_MARKER_SCHEMA = 2
MAILBOX_MARKER_GAME = "Tales of Maj'Eyal"
MAILBOX_MARKER_ADDON = "tome-archipelago"
MAILBOX_MARKER_ROOT = "/archipelago"


def _mailbox_marker_valid(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        marker = read_json(path / MAILBOX_MARKER_NAME, limit=4096)
    except (ValidationError, OSError):
        return False
    return bool(
        isinstance(marker, dict)
        and marker.get("schema") == MAILBOX_MARKER_SCHEMA
        and marker.get("game") == MAILBOX_MARKER_GAME
        and marker.get("addon") == MAILBOX_MARKER_ADDON
        and marker.get("virtual_root") == MAILBOX_MARKER_ROOT
    )


def _mailbox_error(path: Path) -> str:
    return (
        f"{path} is not a Tales of Maj'Eyal Archipelago mailbox. "
        f"Expected a valid {MAILBOX_MARKER_NAME} written by the ToME addon. "
        "Launch ToME once with the matching addon installed, then select the exact "
        "tome/archipelago directory."
    )


def _shop_location_codes(contract: dict) -> list[int]:
    return sorted(loc["code"] for loc in contract.get("locations", []) if loc.get("event") == "shop")


def _scout_snapshot(ctx) -> list[dict]:
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
            continue
        out.append({
            "location": code,
            "item": info.item,
            "item_name": item_name,
            "player": info.player,
            "player_name": ctx.player_names.get(info.player, f"Player {info.player}"),
            "flags": info.flags,
        })
    return out


def _parents(path: Path):
    path = path.resolve()
    yield path
    yield from path.parents


def _candidate_ap_roots(explicit: Path | None):
    seen: set[Path] = set()

    def emit(path: Path | None):
        if not path:
            return
        try:
            resolved = path.expanduser().resolve()
        except OSError:
            return
        if resolved not in seen:
            seen.add(resolved)
            yield resolved

    if explicit:
        yield from emit(explicit)
    env = os.environ.get("ARCHIPELAGO_ROOT")
    if env:
        yield from emit(Path(env))
    for start in (Path.cwd(), Path(__file__).resolve().parent, Path(sys.argv[0]).resolve().parent):
        for parent in _parents(start):
            yield from emit(parent)
    if os.name == "nt":
        program_data = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        yield from emit(program_data / "Archipelago")
    launcher = shutil.which("ArchipelagoLauncher.exe") or shutil.which("ArchipelagoLauncher")
    if launcher:
        yield from emit(Path(launcher).resolve().parent)


def _find_ap(explicit: Path | None) -> tuple[Path | None, Path | None]:
    """Return (source_root, launcher_exe). Either may be None."""
    launcher = None
    for root in _candidate_ap_roots(explicit):
        if (root / "CommonClient.py").is_file():
            return root, launcher
        for name in ("ArchipelagoLauncher.exe", "ArchipelagoLauncher"):
            candidate = root / name
            if candidate.is_file() and launcher is None:
                launcher = candidate
    return None, launcher


def _delegate_to_launcher(launcher: Path, argv: list[str]) -> int:
    # The installed APWorld owns the real CommonClient integration.  The '--'
    # keeps launcher argparse from consuming client-specific options.
    cmd = [str(launcher), "Tales of Maj'Eyal Client", "--", *argv]
    return subprocess.call(cmd)


def _resolve_mailbox(Utils, value: str | None) -> Path:
    if value:
        path = Path(value).expanduser().resolve()
        if not _mailbox_marker_valid(path):
            raise SystemExit(_mailbox_error(path))
        Utils.persistent_store(PERSIST_CATEGORY, PERSIST_MAILBOX_KEY, str(path))
        return path

    cached_value = Utils.persistent_load().get(PERSIST_CATEGORY, {}).get(PERSIST_MAILBOX_KEY)
    cached = Path(cached_value).expanduser().resolve() if cached_value else None
    if cached and _mailbox_marker_valid(cached):
        return cached

    suggest = cached if cached and cached.is_dir() else Path.home()
    while True:
        selected = Utils.open_directory(
            "Select Tales of Maj'Eyal Archipelago mailbox directory",
            str(suggest),
        )
        if not selected:
            raise SystemExit(
                "A valid ToME Archipelago mailbox directory is required. "
                "Launch ToME once with the matching addon installed, then select "
                "its exact tome/archipelago directory."
            )
        path = Path(selected).expanduser().resolve()
        if _mailbox_marker_valid(path):
            Utils.persistent_store(PERSIST_CATEGORY, PERSIST_MAILBOX_KEY, str(path))
            return path
        Utils.messagebox(
            "Invalid ToME Archipelago mailbox",
            _mailbox_error(path),
            error=True,
        )
        if path.is_dir():
            suggest = path


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    bootstrap = argparse.ArgumentParser(add_help=False)
    bootstrap.add_argument("--ap-root", type=Path)
    own, rest = bootstrap.parse_known_args(argv)

    # If CommonClient is already importable, no root discovery is necessary.
    try:
        import CommonClient  # type: ignore
    except ImportError:
        source_root, launcher = _find_ap(own.ap_root)
        if source_root:
            sys.path.insert(0, str(source_root))
        elif launcher:
            # Normal Windows AP installs are frozen and do not expose CommonClient.py.
            # Delegate to the installed custom-world client instead.
            filtered = []
            skip = False
            for i, arg in enumerate(argv):
                if skip:
                    skip = False
                    continue
                if arg == "--ap-root":
                    skip = True
                    continue
                if arg.startswith("--ap-root="):
                    continue
                filtered.append(arg)
            raise SystemExit(_delegate_to_launcher(launcher, filtered))
        else:
            raise SystemExit(
                "Could not find Archipelago 0.6.7. Install tome.apworld and launch the "
                "Tales of Maj'Eyal Client from Archipelago Launcher, set ARCHIPELAGO_ROOT, "
                "or optionally pass --ap-root for a source checkout."
            )

    import Utils
    from CommonClient import (
        CommonContext,
        ClientCommandProcessor,
        get_base_parser,
        gui_enabled,
        handle_url_arg,
        server_loop,
    )
    from NetUtils import ClientStatus

    Utils.init_logging("ToMEClient", exception_logger="Client")

    class Commands(ClientCommandProcessor):
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

    class Context(CommonContext):
        game = "Tales of Maj'Eyal"
        items_handling = 0b111
        command_processor = Commands

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
                self.pending_checks = (
                    set(cached.get("checks", []))
                    if cached and cached.get("identity") == self.identity.to_dict()
                    else set()
                )
                self.dirty = True
                msgs = [{"cmd": "Sync"}]
                shop_codes = [
                    code for code in _shop_location_codes(self.contract)
                    if code in self.server_locations
                ]
                if shop_codes:
                    msgs.append({"cmd": "LocationScouts", "locations": shop_codes, "create_as_hint": 0})
                asyncio.create_task(self.send_msgs(msgs))
            elif cmd == "ReceivedItems":
                if args["index"] == 0:
                    self.history_ready = True
                self.dirty = True
            elif cmd in {"LocationInfo", "RoomUpdate"}:
                self.dirty = True

    async def watcher(ctx):
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

    async def run(args):
        mailbox = _resolve_mailbox(Utils, args.mailbox)
        ctx = Context(args.connect, args.password, mailbox, args.name)
        with exclusive_bridge(ctx.mailbox / "bridge.lock"):
            ctx.server_task = asyncio.create_task(server_loop(ctx), name="AP server")
            if gui_enabled:
                ctx.run_gui()
            ctx.run_cli()
            task = asyncio.create_task(watcher(ctx), name="ToME mailbox")
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

    parser = get_base_parser(description="Tales of Maj'Eyal Archipelago bridge")
    parser.add_argument("--name", default=None, help="Archipelago slot name.")
    parser.add_argument("--mailbox", default=None, help="ToME addon mailbox directory; remembered after first use.")
    parser.add_argument("url", nargs="?", help="archipelago:// connection URL")
    args = parser.parse_args(rest)
    args = handle_url_arg(args, parser=parser)
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
