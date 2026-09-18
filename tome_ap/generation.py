"""Seed construction, exact multiset accounting, scalable locations, and prodigy trees."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, asdict, field
from random import Random
from typing import Any
from .catalog import Catalog, TreeDef
from .locations import (
    BOSS_LOCATIONS, ZONE_LOCATIONS, ZONE_QUEST_LOCATIONS, MAJOR_QUEST_LOCATIONS,
    SHOP_LOCATIONS, VICTORY_LOCATION,
)
from .model import (
    ValidationError, STAT_KEYS, LEVEL_ID_STRIDE, CONTRACT_VERSION,
    level_location_id, digest, integer,
)

@dataclass(frozen=True)
class Settings:
    class_tree_count: int = 6
    generic_tree_count: int = 4
    prodigy_count: int = 5
    starting_ranks: int = 2
    stat_packages_per_stat: int = 10
    level_ceiling: int = 40
    logic_mode: str = "unrestricted"
    zone_exploration_checks: bool = True
    quest_checks: str = "major_and_zone"
    shop_checks: str = "non_progression"
    shop_checks_per_store: int = 3
    early_level_max: int = 10
    t1_t2_boss_priority: bool = True

    def validate(self):
        integer(self.class_tree_count, "class_tree_count", 1, 20)
        integer(self.generic_tree_count, "generic_tree_count", 0, 20)
        integer(self.prodigy_count, "prodigy_count", 0, 20)
        integer(self.starting_ranks, "starting_ranks", 0, 2)
        integer(self.stat_packages_per_stat, "stat_packages_per_stat", 1, 10)
        integer(self.level_ceiling, "level_ceiling", 10, 50)
        integer(self.shop_checks_per_store, "shop_checks_per_store", 1, 3)
        integer(self.early_level_max, "early_level_max", 1, 20)
        if type(self.zone_exploration_checks) is not bool:
            raise ValidationError("zone_exploration_checks must be boolean")
        if type(self.t1_t2_boss_priority) is not bool:
            raise ValidationError("t1_t2_boss_priority must be boolean")
        if self.logic_mode != "unrestricted":
            raise ValidationError(
                "Readiness mode is disabled; only unrestricted generation is supported"
            )
        if self.quest_checks not in {"none", "major", "major_and_zone"}:
            raise ValidationError("Unknown quest check mode")
        if self.shop_checks not in {"off", "non_progression"}:
            raise ValidationError("Unknown shop check mode")

@dataclass(frozen=True)
class LocationDef:
    name: str
    code: int
    level: int
    reward: int
    event: str = "level"
    trigger: dict[str, Any] = field(default_factory=dict)
    placement: str = "default"
    early: bool = False

    def to_dict(self):
        return asdict(self)

@dataclass
class Build:
    catalog_hash: str
    settings: Settings
    random_trees: list[str]
    mandatory_trees: list[str]
    bonus_trees: list[str]
    support_trees: list[str]
    support_precollects: list[str]
    prodigies: list[str]
    prodigy_bonus: dict[str, dict[str, Any]]
    starters: list[str]
    pool: list[str]
    locations: list[LocationDef]

    @property
    def trees(self) -> list[str]:
        # Stable order is useful to the addon and spoiler log.
        return list(dict.fromkeys(
            self.random_trees + self.mandatory_trees + self.bonus_trees + self.support_trees
        ))

    @property
    def precollected(self) -> list[str]:
        return list(self.starters) + list(self.support_precollects)

    def contract(self, catalog: Catalog) -> dict:
        allowed = set(self.pool + self.precollected)
        allowed.add("vitality")
        items = [catalog.items[k].to_dict() for k in sorted(catalog.items)]
        body = dict(
            schema=CONTRACT_VERSION,
            game="Tales of Maj'Eyal",
            game_version=catalog.game_version,
            profile=catalog.profile,
            catalog_hash=self.catalog_hash,
            settings=asdict(self.settings),
            random_trees=self.random_trees,
            mandatory_trees=self.mandatory_trees,
            bonus_trees=self.bonus_trees,
            support_trees=self.support_trees,
            support_precollects=self.support_precollects,
            trees=[asdict(catalog.trees[t]) for t in self.trees],
            prodigies=self.prodigies,
            prodigy_bonus=self.prodigy_bonus,
            starters=self.starters,
            precollected=self.precollected,
            items=items,
            build_item_keys=sorted(allowed),
            locations=[x.to_dict() for x in self.locations],
            full_budget=len(self.pool) + len(self.precollected),
            shuffled_count=len(self.pool),
            goal="age_of_ascendancy_victory",
            remaining_level_policy="award_remaining_level_rewards_on_campaign_victory",
            native_loot_policy="preserve_native_loot_and_direct_stat_rewards; suppress_distributable_progression_rewards",
            online_gameplay="disabled",
            equipment_requirements="bypassed",
        )
        return {**body, "contract_hash": digest(body)}


def allocate_level_rewards(total: int, levels: tuple[int, ...]) -> dict[int, int]:
    """Distribute the remaining location budget across level milestones.

    Dense schedules keep the previous even-per-level behavior.  If enabled
    fixed checks leave fewer rewards than level milestones, use a sparse,
    approximately even schedule instead of manufacturing filler items.
    """
    integer(total, "total", 0)
    if not levels or len(set(levels)) != len(levels):
        raise ValidationError("Need unique level milestones")
    levels = tuple(sorted(levels))
    for lvl in levels:
        integer(lvl, "level", 2, 50)
    if total == 0:
        return {lvl: 0 for lvl in levels}
    if total < len(levels):
        out = {lvl: 0 for lvl in levels}
        if total == 1:
            out[levels[0]] = 1
            return out
        last = len(levels) - 1
        chosen = {round(i * last / (total - 1)) for i in range(total)}
        # Rounding across a monotonic span should be unique when total <= len(levels),
        # but keep a deterministic fallback rather than relying on that detail.
        if len(chosen) != total:
            chosen = set()
            for i in range(total):
                idx = (i * len(levels)) // total
                while idx in chosen and idx < len(levels) - 1:
                    idx += 1
                chosen.add(idx)
        for idx in sorted(chosen):
            out[levels[idx]] = 1
        return out
    base, extra = divmod(total, len(levels))
    if base + bool(extra) > LEVEL_ID_STRIDE:
        raise ValidationError("Configuration exceeds reserved per-level location capacity")
    return {lvl: base + int(i < extra) for i, lvl in enumerate(levels)}


def subtract_copies(names: list[str], removed: list[str]) -> list[str]:
    counts = Counter(names)
    for key in removed:
        if counts[key] <= 0:
            raise ValidationError(f"Cannot remove absent starter {key}")
        counts[key] -= 1
    return [key for key in sorted(counts) for _ in range(counts[key])]


def _compatible(trees: list[TreeDef]) -> bool:
    keys = {t.key for t in trees}
    return all(not keys.intersection(t.conflicts) for t in trees)


def _resolve_prodigy_bonus(catalog: Catalog, prodigies: list[str], active: set[str], rng: Random):
    resolved: dict[str, dict[str, Any]] = {}
    bonus_order: list[str] = []
    for item_key in prodigies:
        rule = catalog.prodigy_rules.get(item_key)
        if not rule:
            continue
        trees = list(rule.bonus_trees)
        if rule.choose_one:
            # Prefer a new category when possible, but a prodigy remains valid if
            # every offered category was already rolled naturally.
            candidates = [t for t in rule.choose_one if t not in active]
            chosen = rng.choice(candidates or list(rule.choose_one))
            trees.append(chosen)
        trees = list(dict.fromkeys(trees))
        for tree in trees:
            if tree not in active:
                active.add(tree)
                bonus_order.append(tree)
        resolved[item_key] = {
            "trees": trees,
            "cleanup_trees": list(rule.cleanup_trees),
            "unlock_mode": rule.unlock_mode,
            "suppress_native_on_learn": rule.suppress_native_on_learn,
        }
    return bonus_order, resolved


def _resolve_support_dependencies(catalog: Catalog, active_tree_keys: list[str]):
    """Resolve transitive hard talent dependencies for an already selected build.

    A dependency may point to another tree or to a talent in the same tree.
    Required talents are precollected exactly once, while newly introduced
    trees contribute all of their remaining ranks to the shuffled pool.
    """
    active = set(active_tree_keys)
    queue = list(active_tree_keys)
    processed: set[str] = set()
    support_order: list[str] = []
    precollects: list[str] = []
    precollect_seen: set[str] = set()

    while queue:
        source = queue.pop(0)
        if source in processed:
            continue
        processed.add(source)
        for dep in catalog.support_dependencies.get(source, []):
            if dep.required_tree not in active:
                active.add(dep.required_tree)
                support_order.append(dep.required_tree)
                queue.append(dep.required_tree)
            elif dep.required_tree not in processed:
                queue.append(dep.required_tree)
            for sym in dep.required_talents:
                key = "talent:" + sym
                if key not in precollect_seen:
                    precollect_seen.add(key)
                    precollects.append(key)

    return support_order, precollects


def create_build(catalog: Catalog, settings: Settings, rng: Random) -> Build:
    settings.validate()
    mandatory = list(catalog.mandatory_trees)
    mandatory_set = set(mandatory)
    class_pool = sorted(
        (t for t in catalog.trees.values() if t.kind == "class" and t.random_eligible and t.key not in mandatory_set),
        key=lambda t: t.key,
    )
    generic_pool = sorted(
        (t for t in catalog.trees.values() if t.kind == "generic" and t.random_eligible and t.key not in mandatory_set),
        key=lambda t: t.key,
    )
    for wanted, pool, label in [
        (settings.class_tree_count, class_pool, "class"),
        (settings.generic_tree_count, generic_pool, "generic"),
    ]:
        if wanted > len(pool):
            raise ValidationError(f"Requested {wanted} {label} trees; catalog supports {len(pool)}")
    if settings.prodigy_count > len(catalog.prodigies):
        raise ValidationError("Not enough approved distinct prodigies")

    for _ in range(2000):
        random_chosen = (
            rng.sample(class_pool, settings.class_tree_count)
            + rng.sample(generic_pool, settings.generic_tree_count)
        )
        all_base = random_chosen + [catalog.trees[t] for t in mandatory]
        starter_candidates = sorted({s for t in random_chosen if t.kind == "class" for s in t.starter_symbols})
        if not starter_candidates:
            # Last-resort fallback: any first class talent.  Runtime metadata marks
            # likely attack talents as starters, so this should be rare.
            starter_candidates = sorted({t.symbols[0] for t in random_chosen if t.kind == "class" and t.symbols})
        if _compatible(all_base) and (not settings.starting_ranks or starter_candidates):
            break
    else:
        raise ValidationError("No compatible build with a usable starter found")

    prodigies = [i.key for i in rng.sample(catalog.prodigies, settings.prodigy_count)]
    active = {t.key for t in random_chosen}.union(mandatory)
    bonus_trees, prodigy_bonus = _resolve_prodigy_bonus(catalog, prodigies, active, rng)
    selected_before_support = [t.key for t in random_chosen] + mandatory + bonus_trees
    support_trees, support_precollects = _resolve_support_dependencies(catalog, selected_before_support)
    active_tree_keys = selected_before_support + support_trees

    full: list[str] = []
    for tree_key in active_tree_keys:
        tree = catalog.trees[tree_key]
        for symbol in tree.symbols:
            item = catalog.items["talent:" + symbol]
            full.extend([item.key] * item.cap)
    for stat in STAT_KEYS:
        full.extend(["stat:" + stat] * settings.stat_packages_per_stat)
    full.extend(prodigies)

    starters: list[str] = []
    if settings.starting_ranks:
        primary = rng.choice(starter_candidates)
        starters.append("talent:" + primary)
        if settings.starting_ranks == 2:
            if catalog.items[starters[0]].cap >= 2:
                starters.append(starters[0])
            elif len(starter_candidates) > 1:
                starters.append("talent:" + rng.choice([s for s in starter_candidates if s != primary]))
            else:
                raise ValidationError("Selected starter cannot provide two ranks")

    precollected = starters + support_precollects
    pool = subtract_copies(full, precollected)

    # Fixed world checks consume the existing reward budget; they never create
    # filler items.  Level checks absorb whatever budget remains.
    primary_specs = list(BOSS_LOCATIONS)
    if settings.zone_exploration_checks:
        primary_specs.extend(ZONE_LOCATIONS)
    if settings.quest_checks in {"major", "major_and_zone"}:
        primary_specs.extend(MAJOR_QUEST_LOCATIONS)
    if settings.quest_checks == "major_and_zone":
        primary_specs.extend(ZONE_QUEST_LOCATIONS)
    if settings.shop_checks == "non_progression":
        primary_specs.extend(
            p for p in SHOP_LOCATIONS
            if int(p.trigger.get("parcel", 0)) <= settings.shop_checks_per_store
        )
    primary_specs.append(VICTORY_LOCATION)

    primary_locations: list[LocationDef] = []
    for p in primary_specs:
        kwargs = p.to_location_kwargs()
        if p.event == "boss" and p.early:
            kwargs["placement"] = "priority" if settings.t1_t2_boss_priority else "default"
        primary_locations.append(LocationDef(**kwargs))

    level_total = len(pool) - len(primary_locations)
    if level_total < 0:
        raise ValidationError(
            f"Enabled fixed checks ({len(primary_locations)}) exceed shuffled rewards ({len(pool)}); "
            "disable some optional checks or increase the build size"
        )
    schedule = allocate_level_rewards(level_total, tuple(range(2, settings.level_ceiling + 1)))
    locations = [
        LocationDef(
            f"Advancement {level:02d} — Reward {i:02d}",
            level_location_id(level, i), level, i, "level", {"level": level},
            "default", level <= settings.early_level_max,
        )
        for level, n in schedule.items()
        for i in range(1, n + 1)
    ]
    locations.extend(primary_locations)
    assert len(pool) == len(locations)

    return Build(
        catalog.hash,
        settings,
        [t.key for t in random_chosen],
        mandatory,
        bonus_trees,
        support_trees,
        support_precollects,
        prodigies,
        prodigy_bonus,
        starters,
        pool,
        locations,
    )


def readiness_thresholds(catalog: Catalog, build: Build, level: int) -> tuple[int, int]:
    """Placement heuristic only; it is not a combat solvability proof."""
    level = build.settings.level_ceiling if level == 0 else level
    integer(level, "readiness level", 2, 50)
    fraction = max(0.0, min(1.0, (level - 2) / (build.settings.level_ceiling - 2)))
    ranks = sum(
        catalog.items["talent:" + s].cap
        for key in build.trees
        for s in catalog.trees[key].symbols
    )
    stat_packages = build.settings.stat_packages_per_stat * 6
    return int(ranks * 0.5 * fraction), int(stat_packages * 0.4 * fraction)
