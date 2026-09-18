"""Tales of Maj'Eyal APWorld. Build with a real runtime-exported catalog."""
from __future__ import annotations
import json
import pkgutil
from BaseClasses import Item, Location, Region, ItemClassification, Tutorial, LocationProgressType
from worlds.AutoWorld import World, WebWorld
from . import components as components
from .options import ToMEOptions
from .core.catalog import Catalog
from .core.generation import Settings, create_build
from .core.locations import PRIMARY_NAME_TO_ID
from .core.model import GAME, LEVEL_ID_STRIDE, level_location_id
from worlds.generic.Rules import add_item_rule

_raw = pkgutil.get_data(__name__, "data/catalog.json")
if not _raw:
    raise RuntimeError("Missing ToME catalog: run tools/build.py with a schema-2 ToME runtime export")
CATALOG = Catalog(json.loads(_raw))

# Internal AP logic event. Neither name is a network item/location, and neither
# is included in the shuffled budget or game-side receipt/check contract.
COMPLETION_EVENT = "Age of Ascendancy Complete"
COMPLETION_LOCATION = "Age of Ascendancy — Completion Event"

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
        completion = ToMELocation(self.player, COMPLETION_LOCATION, None, campaign)
        campaign.locations.append(completion)
        completion.place_locked_item(
            ToMEItem(COMPLETION_EVENT, ItemClassification.progression, None, self.player)
        )

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
        return ToMEItem(name, classification, item.code, self.player)

    def get_filler_item_name(self):
        return CATALOG.items["vitality"].name

    def set_rules(self):
        # Beatability sweeps only collect progression locations. The visible
        # Victory check remains shuffled, so completion must not depend on its
        # reward classification or on CollectionState.locations_checked.
        victory_location = self.get_location("Age of Ascendancy — Victory")
        self.get_location(COMPLETION_LOCATION).access_rule = (
            lambda state: victory_location.can_reach(state)
        )
        self.multiworld.completion_condition[self.player] = (
            lambda state: state.has(COMPLETION_EVENT, self.player)
        )
        # Unrestricted logic intentionally does not model combat difficulty.
        # This event represents modeled reachability, NOT live server victory.
        # CLIENT_GOAL is still sent only after native campaign victory.

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
    def fill_slot_data(self):
        return self.build.contract(CATALOG)

    def write_spoiler(self, spoiler_handle):
        spoiler_handle.write(
            f"\nToME player {self.player}: unrestricted logic (combat solvability is not guaranteed)\n"
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
