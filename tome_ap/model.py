"""Validated, versioned data model; no Archipelago or ToME dependency."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

GAME = "Tales of Maj'Eyal"
PROTOCOL_VERSION = 1
CONTRACT_VERSION = 3
CATALOG_VERSION = 3
MAX_SNAPSHOT_BYTES = 8 * 1024 * 1024
MAX_RECEIPTS = 100_000
STAT_KEYS = ("str", "dex", "con", "mag", "wil", "cun")
STAT_NAMES = ("Strength", "Dexterity", "Constitution", "Magic", "Willpower", "Cunning")
LEVEL_ID_BASE = 782000
LEVEL_ID_STRIDE = 64
MAX_LEVEL = 50

class ValidationError(ValueError):
    pass

def integer(value: Any, name: str, minimum: int = 0, maximum: int = 2**31-1) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValidationError(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value

def text(value: Any, name: str, maximum: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum or "\x00" in value:
        raise ValidationError(f"Invalid {name}")
    return value

def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")

def digest(value: Any) -> str:
    return sha256(canonical_json(value)).hexdigest()

def stable_item_id(key: str) -> int:
    """Deterministic identifiers; collision detection is mandatory in the catalog."""
    text(key, "item key")
    return 1_000_000_000 + int.from_bytes(sha256((GAME + ":" + key).encode()).digest()[:4], "big") % 1_000_000_000

def level_location_id(level: int, reward: int) -> int:
    integer(level, "level", 2, MAX_LEVEL)
    integer(reward, "reward index", 1, LEVEL_ID_STRIDE)
    return LEVEL_ID_BASE + (level - 2) * LEVEL_ID_STRIDE + reward

@dataclass(frozen=True)
class Identity:
    seed_name: str
    team: int
    slot: int
    contract_hash: str

    def __post_init__(self) -> None:
        text(self.seed_name, "seed name", 512)
        integer(self.team, "team")
        integer(self.slot, "slot", 1)
        if len(self.contract_hash) != 64 or any(c not in "0123456789abcdef" for c in self.contract_hash):
            raise ValidationError("Invalid contract hash")

    def to_dict(self) -> dict[str, Any]:
        return dict(seed_name=self.seed_name, team=self.team, slot=self.slot,
                    contract_hash=self.contract_hash)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Identity:
        return cls(data["seed_name"], data["team"], data["slot"], data["contract_hash"])

@dataclass(frozen=True)
class Receipt:
    item: int
    location: int = 0
    player: int = 0
    flags: int = 0

    def __post_init__(self) -> None:
        integer(self.item, "item", 1, 2**53-1)
        integer(self.location, "source location", -(2**53-1), 2**53-1)
        integer(self.player, "source player", 0)
        integer(self.flags, "flags", 0, 255)

    def to_dict(self) -> dict[str, int]:
        return dict(item=self.item, location=self.location, player=self.player, flags=self.flags)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Receipt:
        return cls(data["item"], data.get("location", 0), data.get("player", 0), data.get("flags", 0))
