"""Strict snapshot transport with atomic Python writes and retryable reads."""
from __future__ import annotations
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import tempfile
import time
from typing import Any
from .model import (MAX_SNAPSHOT_BYTES, MAX_RECEIPTS, PROTOCOL_VERSION, CONTRACT_VERSION,
                    Identity, Receipt, ValidationError, canonical_json, digest, integer, text)

def _reject_constants(value):
    raise ValidationError(f"Invalid JSON constant {value}")

def _unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:
            raise ValidationError("Duplicate JSON key")
        result[key]=value
    return result

def read_json(path: Path, limit: int = MAX_SNAPSHOT_BYTES) -> dict[str, Any] | None:
    """Partial files are retried; validation failures are never applied."""
    try:
        with path.open("rb") as f:
            raw = f.read(limit + 1)
        if len(raw) > limit:
            raise ValidationError(f"Mailbox exceeds {limit} bytes")
        value = json.loads(raw.decode("utf-8"), parse_constant=_reject_constants, object_pairs_hook=_unique_object)
        if not isinstance(value, dict):
            raise ValidationError("Mailbox root must be an object")
        return value
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, json.JSONDecodeError):
        return None

def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json(value) + b"\n"
    if len(data) > MAX_SNAPSHOT_BYTES:
        raise ValidationError("Snapshot too large")
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        # ToME must close its read handle promptly. Windows readers may briefly
        # block replacement; leave the preceding snapshot intact until retry.
        for attempt in range(6):
            try:
                os.replace(temp, path)
                break
            except PermissionError:
                if attempt == 5:
                    raise
                time.sleep(0.02 * (attempt + 1))
    finally:
        try:
            os.unlink(temp)
        except FileNotFoundError:
            pass

def validate_contract(contract: dict) -> dict:
    body = {k:v for k,v in contract.items() if k != "contract_hash"}
    if contract.get("schema") != CONTRACT_VERSION or contract.get("contract_hash") != digest(body):
        raise ValidationError("Invalid contract schema/hash")
    ids, keys = set(), set()
    for item in contract["items"]:
        integer(item["code"], "item code", 1)
        if item["code"] in ids or item["key"] in keys:
            raise ValidationError("Duplicate contract item")
        ids.add(item["code"]); keys.add(item["key"])
    locs = [integer(loc["code"], "location code", 1) for loc in contract["locations"]]
    if len(locs) != len(set(locs)) or len(locs) != contract["shuffled_count"]:
        raise ValidationError("Invalid active-location budget")
    return contract

def _validate_scouts(scouted_locations: list[dict] | None, active_locations: set[int]) -> list[dict]:
    scouts = [] if scouted_locations is None else scouted_locations
    if not isinstance(scouts, list) or len(scouts) > len(active_locations):
        raise ValidationError("Invalid scouted-location list")
    seen: set[int] = set()
    for scout in scouts:
        if not isinstance(scout, dict):
            raise ValidationError("Invalid scouted-location record")
        location = integer(scout.get("location"), "scouted location", 1, 2**53-1)
        if location not in active_locations or location in seen:
            raise ValidationError("Unknown or duplicate scouted location")
        seen.add(location)
        integer(scout.get("item"), "scouted item", 1, 2**53-1)
        integer(scout.get("player"), "scouted recipient", 1)
        integer(scout.get("flags", 0), "scouted flags", 0, 255)
        text(scout.get("item_name"), "scouted item name", 512)
        text(scout.get("player_name"), "scouted player name", 256)
    return scouts

def client_snapshot(identity: Identity, contract: dict, receipts: list[Receipt], checked: set[int],
                    revision: int, connected: bool, scouted_locations: list[dict] | None = None) -> dict:
    validate_contract(contract)
    if identity.contract_hash != contract["contract_hash"]:
        raise ValidationError("Identity and contract differ")
    integer(revision, "revision")
    if len(receipts) > MAX_RECEIPTS:
        raise ValidationError("Receipt limit exceeded")
    allowed = {i["code"] for i in contract["items"]}
    if any(r.item not in allowed for r in receipts):
        raise ValidationError("Server sent an item not represented in this seed contract")
    active_locations = {loc["code"] for loc in contract["locations"]}
    scouts = _validate_scouts(scouted_locations, active_locations)
    return dict(protocol=PROTOCOL_VERSION, identity=identity.to_dict(), contract=contract,
                receipts=[r.to_dict() for r in receipts], checked_locations=sorted(checked),
                scouted_locations=scouts, revision=revision, connected=bool(connected),
                written_at=time.time(), complete=True)

def validate_game_snapshot(value: dict, identity: Identity, active: set[int]) -> dict:
    if value.get("protocol") != PROTOCOL_VERSION or value.get("complete") is not True:
        raise ValidationError("Incomplete/unsupported game snapshot")
    if Identity.from_dict(value["identity"]) != identity:
        raise ValidationError("Wrong AP seed, team, slot, or build contract")
    integer(value["applied_count"], "applied receipt count", 0, MAX_RECEIPTS)
    integer(value["revision"], "game revision")
    checks = value.get("checks", [])
    if not isinstance(checks, list) or len(checks) > len(active):
        raise ValidationError("Invalid check list")
    if any(type(c) is not int or c not in active for c in checks):
        raise ValidationError("Game attempted to send a location absent from the seed")
    if type(value.get("goal")) is not bool:
        raise ValidationError("Goal must be boolean")
    return value

@contextmanager
def exclusive_bridge(path: Path):
    """OS file lock, released on process death; one writer per mailbox."""
    path.parent.mkdir(parents=True, exist_ok=True)
    file = path.open("a+b")
    file.seek(0); file.write(b"0"); file.flush(); file.seek(0)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        file.close()
        raise ValidationError("Another bridge is already using this mailbox") from None
    try:
        yield
    finally:
        if os.name == "nt":
            import msvcrt
            file.seek(0); msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)
        file.close()
