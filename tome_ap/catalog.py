"""Compile a stable AP catalog from ToME's runtime metadata export.

The runtime export is authoritative for talent IDs/caps and the set of installed
player subclasses.  A small reviewed profile only expresses AP-specific policy:
mandatory trees, deliberate exclusions, and prodigy -> bonus-tree behavior.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any
from .model import (
    ValidationError, CATALOG_VERSION, STAT_KEYS, STAT_NAMES, digest, integer,
    text, stable_item_id,
)

SYMBOL = re.compile(r"^T_[A-Z0-9_]+$")
TREE_KEY = re.compile(r"^[a-z0-9][a-z0-9_'-]*/[a-z0-9][a-z0-9_'-]*$")

@dataclass(frozen=True)
class ItemDef:
    key: str
    name: str
    code: int
    kind: str
    symbol: str = ""
    tree: str = ""
    cap: int = 1
    amount: int = 0
    stat: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))

@dataclass(frozen=True)
class TreeDef:
    key: str
    kind: str
    name: str
    symbols: tuple[str, ...]
    resources: tuple[str, ...] = ()
    starter_symbols: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    random_eligible: bool = True

@dataclass(frozen=True)
class SupportDependency:
    source_tree: str
    required_tree: str
    required_talents: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_tree": self.source_tree,
            "required_tree": self.required_tree,
            "required_talents": list(self.required_talents),
        }

@dataclass(frozen=True)
class ProdigyRule:
    item_key: str
    bonus_trees: tuple[str, ...] = ()
    choose_one: tuple[str, ...] = ()
    cleanup_trees: tuple[str, ...] = ()
    unlock_mode: str = "immediate"  # immediate or native
    suppress_native_on_learn: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_key": self.item_key,
            "bonus_trees": list(self.bonus_trees),
            "choose_one": list(self.choose_one),
            "cleanup_trees": list(self.cleanup_trees),
            "unlock_mode": self.unlock_mode,
            "suppress_native_on_learn": self.suppress_native_on_learn,
        }

class Catalog:
    def __init__(self, data: dict[str, Any]):
        if data.get("schema") != CATALOG_VERSION:
            raise ValidationError("Unsupported catalog schema")
        self.data = data
        self.hash = digest(data)
        self.game_version = text(data["game_version"], "game version")
        self.profile = text(data["profile"], "profile")
        self.items: dict[str, ItemDef] = {}
        self.by_id: dict[int, ItemDef] = {}
        self.by_name: dict[str, ItemDef] = {}
        self.trees: dict[str, TreeDef] = {}
        self.prodigies: list[ItemDef] = []
        self.prodigy_rules: dict[str, ProdigyRule] = {}
        self.support_dependencies: dict[str, list[SupportDependency]] = {}
        self.mandatory_trees = tuple(data.get("mandatory_trees", []))

        for raw in data["items"]:
            item = ItemDef(**raw)
            integer(item.code, "item code", 1)
            integer(item.cap, "item cap", 1, 100000)
            text(item.name, "item name")
            if item.kind not in {"talent", "stat", "prodigy", "vitality"}:
                raise ValidationError(f"Unknown item kind {item.kind}")
            if item.kind in {"talent", "prodigy"} and not SYMBOL.fullmatch(item.symbol):
                raise ValidationError(f"Invalid talent symbol: {item.symbol}")
            if item.code in self.by_id or item.key in self.items or item.name in self.by_name:
                raise ValidationError(f"Duplicate item key/name/ID: {item.key}")
            if item.kind == "stat" and (item.stat not in STAT_KEYS or item.amount != 5):
                raise ValidationError("Stat items must grant +5 to a named stat")
            self.items[item.key] = self.by_id[item.code] = self.by_name[item.name] = item
            if item.kind == "prodigy":
                self.prodigies.append(item)

        for raw in data["trees"]:
            raw = dict(raw)
            for field in ("symbols", "resources", "starter_symbols", "conflicts"):
                raw[field] = tuple(raw.get(field, []))
            tree = TreeDef(**raw)
            if tree.kind not in {"class", "generic"} or tree.key in self.trees or not tree.symbols:
                raise ValidationError(f"Invalid or duplicate tree: {tree.key}")
            if not TREE_KEY.fullmatch(tree.key):
                raise ValidationError(f"Invalid tree key: {tree.key}")
            if len(tree.symbols) != len(set(tree.symbols)):
                raise ValidationError(f"Duplicate talent in {tree.key}")
            for sym in tree.symbols:
                item = self.items.get("talent:" + sym)
                if not item or item.tree != tree.key:
                    raise ValidationError(f"Missing or mismatched talent {sym}")
            if not set(tree.starter_symbols).issubset(tree.symbols):
                raise ValidationError(f"Starter not in tree {tree.key}")
            self.trees[tree.key] = tree

        for key in self.mandatory_trees:
            if key not in self.trees:
                raise ValidationError(f"Mandatory tree missing from catalog: {key}")

        for raw in data.get("prodigy_rules", []):
            raw = dict(raw)
            raw["bonus_trees"] = tuple(raw.get("bonus_trees", []))
            raw["choose_one"] = tuple(raw.get("choose_one", []))
            raw["cleanup_trees"] = tuple(raw.get("cleanup_trees", []))
            rule = ProdigyRule(**raw)
            if rule.item_key in self.prodigy_rules or rule.item_key not in self.items:
                raise ValidationError(f"Invalid prodigy rule {rule.item_key}")
            if self.items[rule.item_key].kind != "prodigy":
                raise ValidationError(f"Prodigy rule targets non-prodigy {rule.item_key}")
            if rule.unlock_mode not in {"immediate", "native"}:
                raise ValidationError(f"Invalid unlock mode for {rule.item_key}")
            for tree in (*rule.bonus_trees, *rule.choose_one, *rule.cleanup_trees):
                if tree not in self.trees:
                    raise ValidationError(f"Prodigy rule references missing tree {tree}")
            self.prodigy_rules[rule.item_key] = rule

        for raw in data.get("support_dependencies", []):
            raw = dict(raw)
            raw["required_talents"] = tuple(raw.get("required_talents", []))
            dep = SupportDependency(**raw)
            if dep.source_tree not in self.trees:
                raise ValidationError(f"Support dependency source tree missing: {dep.source_tree}")
            if dep.required_tree not in self.trees:
                raise ValidationError(f"Support dependency required tree missing: {dep.required_tree}")
            if not dep.required_talents:
                raise ValidationError(f"Support dependency has no enabling talent: {dep.source_tree}")
            for sym in dep.required_talents:
                if not SYMBOL.fullmatch(sym):
                    raise ValidationError(f"Invalid support talent symbol: {sym}")
                item = self.items.get("talent:" + sym)
                if not item or item.tree != dep.required_tree:
                    raise ValidationError(
                        f"Support dependency {dep.source_tree} requires {sym}, "
                        f"but it is not owned by {dep.required_tree}"
                    )
            bucket = self.support_dependencies.setdefault(dep.source_tree, [])
            if dep in bucket:
                raise ValidationError(f"Duplicate support dependency for {dep.source_tree}")
            bucket.append(dep)

        for key in STAT_KEYS:
            if "stat:" + key not in self.items:
                raise ValidationError("Catalog must include all six stat packages")
        if "vitality" not in self.items:
            raise ValidationError("Catalog needs repeatable fallback")
        self.prodigies.sort(key=lambda i: i.key)

    @classmethod
    def load(cls, path: Path) -> "Catalog":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def to_json(self) -> str:
        return json.dumps(self.data, ensure_ascii=False, indent=2) + "\n"


def _runtime_trees(export: dict[str, Any]) -> tuple[dict[str, dict], dict[str, dict]]:
    available: dict[str, dict] = {}
    for tree in export.get("trees", []):
        key = tree.get("key")
        if not isinstance(key, str) or key in available:
            raise ValidationError(f"Duplicate/invalid exported tree {key!r}")
        available[key] = tree
    talents: dict[str, dict] = {}
    for talent in export.get("talents", []):
        sym = talent.get("symbol")
        if not isinstance(sym, str) or sym in talents:
            raise ValidationError(f"Duplicate/invalid exported talent {sym!r}")
        talents[sym] = talent
    return available, talents


def compile_catalog(export: dict[str, Any], profile: dict[str, Any]) -> Catalog:
    """Compile the full installed player-tree catalog.

    Export schema 2 adds `player_trees`, resource use, and real `t.uber`
    prodigy markers.  Schema 1 is intentionally rejected for the full profile
    so an old narrow/ambiguous export cannot silently become a release catalog.
    """
    if export.get("schema") != 2:
        raise ValidationError(
            "The full catalog requires runtime-export schema 2. Install the current addon, "
            "restart ToME, and regenerate runtime-export.json."
        )
    available, talents = _runtime_trees(export)
    if profile.get("mode") != "runtime-player-trees":
        raise ValidationError("Full compiler requires profile mode runtime-player-trees")

    player_tree_keys = export.get("player_trees")
    if not isinstance(player_tree_keys, list) or not player_tree_keys:
        raise ValidationError("Runtime export contains no player_trees")
    if len(player_tree_keys) != len(set(player_tree_keys)):
        raise ValidationError("runtime player_trees contains duplicates")

    excluded_trees = set(profile.get("exclude_trees", []))
    mandatory_trees = tuple(profile.get("mandatory_trees", ["technique/combat-training"]))
    excluded_prodigies = set(profile.get("exclude_prodigies", []))
    runtime_prodigies = [t for t in talents.values() if t.get("prodigy") is True]
    if not runtime_prodigies:
        raise ValidationError("Runtime export contains no actual prodigies (t.uber=true)")
    available_prodigies = {
        t["symbol"] for t in runtime_prodigies if t["symbol"] not in excluded_prodigies
    }
    # Do this BEFORE computing wanted and its support-dependency closure.
    # Uninstalled/excluded prodigies must not require their optional categories.
    prodigy_policy = {
        symbol: rule for symbol, rule in profile.get("prodigy_rules", {}).items()
        if symbol in available_prodigies
    }
    support_policy = profile.get("support_dependencies", {})
    if not isinstance(support_policy, dict):
        raise ValidationError("support_dependencies must be an object keyed by source tree")

    wanted = {key for key in player_tree_keys if key not in excluded_trees}
    wanted.update(mandatory_trees)
    for symbol, rule in prodigy_policy.items():
        for tree in rule.get("bonus_trees", []):
            wanted.add(tree)
        for tree in rule.get("choose_one", []):
            wanted.add(tree)
        for tree in rule.get("cleanup_trees", []):
            wanted.add(tree)

    # Support dependencies are transitive: a support tree may itself need
    # another enabling tree/rank. Only dependencies reachable from an active
    # player/prodigy/mandatory tree are compiled into this installation.
    changed = True
    while changed:
        changed = False
        for source_tree, entries in support_policy.items():
            if source_tree not in wanted:
                continue
            if not isinstance(entries, list):
                raise ValidationError(f"Support dependency list expected for {source_tree}")
            for raw in entries:
                if not isinstance(raw, dict) or not isinstance(raw.get("tree"), str):
                    raise ValidationError(f"Invalid support dependency for {source_tree}")
                required_tree = raw["tree"]
                if required_tree not in wanted:
                    wanted.add(required_tree)
                    changed = True

    missing = sorted(wanted - available.keys())
    if missing:
        raise ValidationError("Runtime export is missing required AP trees: " + ", ".join(missing))

    tree_defs: list[dict[str, Any]] = []
    item_defs: list[dict[str, Any]] = []
    seen_symbols: set[str] = set()
    included_symbols: set[str] = set()

    for tree_key in sorted(wanted):
        source = available[tree_key]
        syms = list(source.get("symbols", []))
        if not syms:
            raise ValidationError(f"Empty category {tree_key}")
        starters: list[str] = []
        for sym in syms:
            if sym in seen_symbols:
                # Some helper categories duplicate a talent from a real player tree.
                # Player trees must have one canonical owner in the runtime export.
                raise ValidationError(f"Talent shared by selected categories: {sym}")
            seen_symbols.add(sym)
            try:
                t = talents[sym]
            except KeyError as exc:
                raise ValidationError(f"Tree {tree_key} references absent talent {sym}") from exc
            integer(t["cap"], "raw talent cap", 1, 20)
            key = "talent:" + sym
            item_defs.append(ItemDef(
                key, f'{source.get("name", tree_key)}: {t["name"]}', stable_item_id(key),
                "talent", sym, tree_key, t["cap"]
            ).to_dict())
            included_symbols.add(sym)
            if t.get("starter") is True:
                starters.append(sym)
        tree_defs.append(dict(
            key=tree_key,
            name=source.get("name", tree_key),
            kind="generic" if source.get("generic") else "class",
            symbols=syms,
            resources=sorted(set(source.get("resources", []))),
            starter_symbols=starters,
            conflicts=[],
            random_eligible=tree_key in set(player_tree_keys),
        ))

    prodigy_keys: set[str] = set()
    for t in sorted(runtime_prodigies, key=lambda x: x["symbol"]):
        sym = t["symbol"]
        if sym in excluded_prodigies:
            continue
        key = "prodigy:" + sym
        item_defs.append(ItemDef(
            key, "Prodigy: " + t["name"], stable_item_id(key), "prodigy", sym
        ).to_dict())
        prodigy_keys.add(key)

    rules: list[dict[str, Any]] = []
    for sym, raw in sorted(prodigy_policy.items()):
        key = "prodigy:" + sym
        if key not in prodigy_keys:
            # Policy may describe a DLC prodigy that is not installed.  Omit it.
            continue
        rule = ProdigyRule(
            item_key=key,
            bonus_trees=tuple(raw.get("bonus_trees", [])),
            choose_one=tuple(raw.get("choose_one", [])),
            cleanup_trees=tuple(raw.get("cleanup_trees", [])),
            unlock_mode=raw.get("unlock_mode", "immediate"),
            suppress_native_on_learn=bool(raw.get("suppress_native_on_learn", False)),
        )
        rules.append(rule.to_dict())

    support_rules: list[dict[str, Any]] = []
    for source_tree, entries in sorted(support_policy.items()):
        if source_tree not in wanted:
            continue
        for raw in entries:
            required_tree = raw["tree"]
            required_talents = tuple(raw.get("talents", []))
            if not required_talents:
                raise ValidationError(f"Support dependency has no enabling talent: {source_tree}")
            owner_symbols = set(available[required_tree].get("symbols", []))
            for sym in required_talents:
                if sym not in owner_symbols:
                    raise ValidationError(
                        f"Support dependency {source_tree} requires {sym}, "
                        f"but runtime tree {required_tree} does not contain it"
                    )
            support_rules.append(SupportDependency(
                source_tree=source_tree, required_tree=required_tree,
                required_talents=required_talents,
            ).to_dict())

    for stat, name in zip(STAT_KEYS, STAT_NAMES):
        key = "stat:" + stat
        item_defs.append(ItemDef(
            key, "+5 " + name, stable_item_id(key), "stat", cap=10, amount=5, stat=stat
        ).to_dict())
    item_defs.append(ItemDef(
        "vitality", "Vitality: +1 maximum life", stable_item_id("vitality"),
        "vitality", cap=2**15, amount=1
    ).to_dict())

    return Catalog(dict(
        schema=CATALOG_VERSION,
        game_version=export["game_version"],
        profile=profile["name"],
        mandatory_trees=list(mandatory_trees),
        trees=tree_defs,
        prodigy_rules=rules,
        support_dependencies=support_rules,
        items=sorted(item_defs, key=lambda i: i["key"]),
    ))
