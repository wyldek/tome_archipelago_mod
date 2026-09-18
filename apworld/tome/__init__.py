"""Tales of Maj'Eyal APWorld. Build with a real runtime-exported catalog."""
from __future__ import annotations
import json
import pkgutil
from BaseClasses import Item, Location, Region, ItemClassification, Tutorial, LocationProgressType
from worlds.AutoWorld import World, WebWorld
from . import components as components
from .options import ToMEOptions
from .core.catalog import Catalog
from .core.generation import Settings, create_build, readiness_thresholds
from .core.locations import PRIMARY_NAME_TO_ID
from .core.model import GAME, LEVEL_ID_STRIDE, level_location_id
from worlds.generic.Rules import add_item_rule

_raw = pkgutil.get_data(__name__, "data/catalog.json")
if not _raw:
    raise RuntimeError("Missing ToME catalog: run tools/build.py with a schema-2 ToME runtime export")
CATALOG = Catalog(json.loads(_raw))

class ToMEItem(Item):
    game = GAME

class ToMELocation(Location):
    game = GAME

class ToMEWeb(WebWorld):
    theme = "stone"
    tutorials = [Tutorial(
        "ToME Archipelago Setup",
        "Install the ToME addon and Archipelago bridge.",
        "English", "setup_en.md", "setup/en", ["ToME AP contributors"],
    )]

class ToMEWorld(World):
    """A seed-generated Adventurer receiving specific talent ranks, stat packages,
    and prodigies.  Native ToME gear and boss loot are never replaced.
    """
    game = GAME
    web = ToMEWeb()
    options_dataclass = ToMEOptions
    options: ToMEOptions
    item_name_to_id = {item.name: item.code for item in CATALOG.items.values()}
    location_name_to_id = {
        f"Advancement {level:02d} — Reward {reward:02d}": level_location_id(level, reward)
        for level in range(2, 51)
        for reward in range(1, LEVEL_ID_STRIDE + 1)
    }
    location_name_to_id.update(PRIMARY_NAME_TO_ID)

    def generate_early(self):
        for name in ("start_inventory", "start_inventory_from_pool", "item_links", "exclude_locations"):
            option = getattr(self.options, name, None)
            if option is not None and getattr(option, "value", None):
                raise ValueError(
                    f"ToME does not support nonempty {name}; use starting_ranks instead of custom starters"
                )
        settings = Settings(
            class_tree_count=self.options.class_tree_count.value,
            generic_tree_count=self.options.generic_tree_count.value,
            prodigy_count=self.options.prodigy_count.value,
            starting_ranks=self.options.starting_ranks.value,
            level_ceiling=self.options.level_ceiling.value,
            logic_mode="readiness" if self.options.logic_mode.value == 1 else "unrestricted",
            zone_exploration_checks=bool(self.options.zone_exploration_checks.value),
            quest_checks={0: "none", 1: "major", 2: "major_and_zone"}[self.options.quest_checks.value],
            shop_checks={0: "off", 1: "non_progression"}[self.options.shop_checks.value],
            shop_checks_per_store=self.options.shop_checks_per_store.value,
            early_level_max=self.options.early_level_max.value,
            t1_t2_boss_priority=bool(self.options.t1_t2_boss_priority.value),
        )
        self.build = create_build(CATALOG, settings, self.random)

    def create_regions(self):
        menu = Region("Menu", self.player, self.multiworld)
        campaign = Region("Age of Ascendancy", self.player, self.multiworld)
        menu.connect(campaign)
        self.multiworld.regions.extend([menu, campaign])
        for loc in self.build.locations:
            ap_loc = ToMELocation(self.player, loc.name, loc.code, campaign)
            if loc.placement == "priority":
                ap_loc.progress_type = LocationProgressType.PRIORITY
            campaign.locations.append(ap_loc)

    def create_items(self):
        for key in self.build.precollected:
            self.multiworld.push_precollected(self.create_item(CATALOG.items[key].name))
        self.multiworld.itempool.extend(
            self.create_item(CATALOG.items[key].name) for key in self.build.pool
        )
        assert len(self.build.pool) == len(self.build.locations)

    def create_item(self, name):
        item = CATALOG.by_name[name]
        classification = ItemClassification.filler if item.kind == "vitality" else ItemClassification.useful
        if self.build.settings.logic_mode == "readiness":
            bonus_gate_items = {
                prodigy_key
                for prodigy_key, rule in self.build.prodigy_bonus.items()
                if any(tree in self.build.bonus_trees for tree in rule.get("trees", []))
            }
            if (
                item.kind == "stat"
                or (item.kind == "talent" and item.tree in self.build.trees)
                or item.key in bonus_gate_items
            ):
                classification = ItemClassification.progression
        return ToMEItem(name, classification, item.code, self.player)

    def get_filler_item_name(self):
        return CATALOG.items["vitality"].name

    def set_rules(self):
        # Keep the network Victory check as an ordinary item-bearing location.
        # For generator logic, the slot is complete once that location has been
        # swept/checked. The real client still reports CLIENT_GOAL only after
        # native Age of Ascendancy victory, so server completion is never faked.
        victory_location = self.get_location("Age of Ascendancy — Victory")
        self.multiworld.completion_condition[self.player] = (
            lambda state: victory_location in state.locations_checked
        )

        # AP's generic early-item distributor considers every logically reachable
        # location. Unrestricted ToME intentionally has very light access logic,
        # so explicitly requested early items need a physical-pacing guard: only
        # configured early-level rewards and curated T1/T2 exploration/quest/boss checks may
        # contain them. This applies to early items belonging to any world.
        def explicitly_requested_early(item):
            return bool(
                self.multiworld.early_items[item.player].get(item.name, 0)
                or self.multiworld.local_early_items[item.player].get(item.name, 0)
            )

        for loc_def in self.build.locations:
            location = self.get_location(loc_def.name)
            if loc_def.placement == "non_progression":
                # Paid shops are allowed to contain useful/filler/trap items,
                # but never logical advancement from any world.
                add_item_rule(location, lambda item: not item.advancement)
            if not loc_def.early:
                add_item_rule(
                    location,
                    lambda item: not explicitly_requested_early(item),
                )
        if self.build.settings.logic_mode == "readiness":
            talents = [
                CATALOG.items["talent:" + s]
                for key in self.build.trees
                for s in CATALOG.trees[key].symbols
            ]
            stats = [i for i in CATALOG.items.values() if i.kind == "stat"]

            bonus_gates = {}
            for prodigy_key, bonus in self.build.prodigy_bonus.items():
                for tree in bonus.get("trees", []):
                    if tree in self.build.bonus_trees:
                        bonus_gates.setdefault(tree, []).append(CATALOG.items[prodigy_key].name)

            def talent_count(state):
                total = 0
                for item in talents:
                    gates = bonus_gates.get(item.tree)
                    if gates and not any(state.has(name, self.player) for name in gates):
                        continue
                    total += min(item.cap, state.count(item.name, self.player))
                return total

            def rule_for(level):
                talent_need, stat_need = readiness_thresholds(CATALOG, self.build, level)
                return lambda state: (
                    talent_count(state) >= talent_need
                    and sum(
                        min(self.build.settings.stat_packages_per_stat, state.count(i.name, self.player))
                        for i in stats
                    ) >= stat_need
                )

            for loc in self.build.locations:
                self.get_location(loc.name).access_rule = rule_for(loc.level)

    def fill_slot_data(self):
        return self.build.contract(CATALOG)

    def write_spoiler(self, spoiler_handle):
        spoiler_handle.write(
            f"\nToME player {self.player}: EXPERIMENTAL {self.build.settings.logic_mode} combat logic\n"
        )
        spoiler_handle.write("Random trees: " + ", ".join(self.build.random_trees) + "\n")
        spoiler_handle.write("Mandatory trees: " + ", ".join(self.build.mandatory_trees) + "\n")
        if self.build.bonus_trees:
            spoiler_handle.write("Prodigy bonus trees: " + ", ".join(self.build.bonus_trees) + "\n")
        if self.build.support_trees:
            spoiler_handle.write("Dependency support trees: " + ", ".join(self.build.support_trees) + "\n")
        if self.build.support_precollects:
            spoiler_handle.write("Free dependency ranks: " + ", ".join(self.build.support_precollects) + "\n")
        spoiler_handle.write("Prodigies: " + ", ".join(self.build.prodigies) + "\n")
        spoiler_handle.write(
            f"{len(self.build.pool)} shuffled items / locations; "
            f"{len(self.build.precollected)} total precollected ranks "
            f"({len(self.build.starters)} normal starters + {len(self.build.support_precollects)} dependency ranks)\n"
        )
