"""Run inside the pinned Archipelago checkout; these use real AP classes/fill."""
from argparse import Namespace
from collections import Counter
import unittest

from BaseClasses import CollectionState, Item, ItemClassification, Location, MultiWorld, Region
from Fill import distribute_items_restrictive
from test.general import TestWorld, gen_steps, setup_multiworld
from worlds.AutoWorld import call_all
from worlds.generic.Rules import add_item_rule

from .. import CATALOG, COMPLETION_EVENT, COMPLETION_LOCATION, ToMEItem, ToMEWorld
from ..core.model import CATALOG_VERSION, CONTRACT_VERSION
from .bases import ToMETestBase


def assert_early_ranks_placed(test, multiworld, world):
    requested = Counter(CATALOG.items[key].name for key in world.build.early_talents)
    local_early = {
        loc.name for loc in world.build.locations
        if loc.early and loc.placement == "default"
    }
    for name, count in requested.items():
        chosen = world._early_placed_ranks[name]
        test.assertEqual(len(chosen), count, name)
        test.assertEqual(len({id(item) for item in chosen}), count, name)
        for item in chosen:
            test.assertIsNotNone(item.location, name)
            test.assertTrue(item.location.locked, name)
            if item.location.player == world.player:
                test.assertIn(item.location.name, local_early, name)


def assert_remaining_mastery_copies_legal_late(test, multiworld, world):
    name = CATALOG.items["talent:T_WEAPON_COMBAT"].name
    chosen = {id(item) for item in world._early_placed_ranks[name]}
    remaining = [item for item in multiworld.itempool
                 if item.player == world.player and item.name == name and id(item) not in chosen]
    test.assertGreaterEqual(len(remaining), 1)
    late = next(multiworld.get_location(loc.name, world.player) for loc in world.build.locations
                if not loc.early and loc.placement == "default")
    test.assertTrue(all(late.item_rule(item) for item in remaining))


class TestDefaultWorld(ToMETestBase):
    @property
    def run_default_tests(self):
        # Upstream skips inherited checks for an empty options dict by default.
        # A release must actually fill/test our default configuration too.
        return True

    def test_exact_accounting(self):
        self.assertEqual(len(self.world.build.pool), len(self.world.build.locations))
        network_locations = [loc for loc in self.multiworld.get_locations() if loc.address is not None]
        self.assertEqual(len(network_locations), len(self.world.build.pool))

    def test_catalog_v4_contract_v3_boundary(self):
        self.assertEqual(CATALOG.data["schema"], CATALOG_VERSION)
        self.assertEqual(CATALOG_VERSION, 4)
        contract = self.world.fill_slot_data()
        self.assertEqual(contract["schema"], CONTRACT_VERSION)
        self.assertEqual(CONTRACT_VERSION, 3)
        self.assertNotIn("capability_providers", contract)
        self.assertNotIn("functional_dependencies", contract)
        self.assertNotIn("anchor_talents", contract)


class TestSmallWorld(ToMETestBase):
    options = {"class_tree_count": 2, "generic_tree_count": 2, "shop_checks": "off"}


class TestMinimalWorld(ToMETestBase):
    options = {"class_tree_count": 1, "generic_tree_count": 0, "prodigy_count": 0,
               "shop_checks": "off", "quest_checks": "none", "zone_exploration_checks": False}


class TestNoStarters(ToMETestBase):
    options = {"starting_ranks": 0}


class TestTightEarlyWindow(ToMETestBase):
    options = {"class_tree_count": 1, "generic_tree_count": 0,
               "prodigy_count": 0, "starting_ranks": 0, "shop_checks": "off",
               "early_level_max": 3, "zone_exploration_checks": False,
               "quest_checks": "none"}

    def test_native_fill_places_early_ranks_and_leaves_other_copies_legal(self):
        early_locations = [loc for loc in self.world.build.locations
                           if loc.early and loc.placement == "default"]
        priority_bosses = [loc for loc in self.world.build.locations
                           if loc.early and loc.placement == "priority"]
        self.assertEqual(len(priority_bosses),
                         10 if self.options.get("t1_t2_boss_priority", True) else 0)
        self.assertGreaterEqual(len(early_locations), len(self.world.build.early_talents))
        distribute_items_restrictive(self.multiworld)
        assert_early_ranks_placed(self, self.multiworld, self.world)
        assert_remaining_mastery_copies_legal_late(self, self.multiworld, self.world)


class TestTightEarlyWindowNoBossPriority(TestTightEarlyWindow):
    options = {**TestTightEarlyWindow.options, "t1_t2_boss_priority": False}


class TestCompletionEvent(ToMETestBase):
    def test_completion_independent_of_visible_victory_reward(self):
        victory = self.world.get_location("Age of Ascendancy — Victory")
        for classification in (ItemClassification.filler, ItemClassification.useful,
                               ItemClassification.progression):
            with self.subTest(classification=classification):
                reward = ToMEItem("Test Victory Reward", classification, 1, self.player)
                victory.item = reward
                reward.location = victory
                state = CollectionState(self.multiworld)
                self.assertFalse(state.has(COMPLETION_EVENT, self.player))
                self.assertTrue(self.multiworld.can_beat_game(state))
                state.sweep_for_advancements()
                self.assertTrue(state.has(COMPLETION_EVENT, self.player))

    def test_event_follows_modeled_victory_access(self):
        victory = self.world.get_location("Age of Ascendancy — Victory")
        victory.access_rule = lambda state: False
        state = CollectionState(self.multiworld)
        state.sweep_for_advancements()
        self.assertFalse(state.has(COMPLETION_EVENT, self.player))
        self.assertFalse(self.multiworld.can_beat_game(state))
        victory.access_rule = lambda state: True
        self.assertTrue(self.multiworld.can_beat_game(CollectionState(self.multiworld)))

    def test_event_is_not_a_network_check_or_receipt(self):
        event = self.world.get_location(COMPLETION_LOCATION)
        self.assertIsNone(event.address)
        self.assertIsNone(event.item.code)
        self.assertTrue(event.locked)
        self.assertNotIn(COMPLETION_LOCATION, self.world.location_name_to_id)
        self.assertNotIn(COMPLETION_EVENT, self.world.item_name_to_id)
        contract = self.world.fill_slot_data()
        self.assertEqual(len(contract["locations"]), len(self.world.build.pool))
        self.assertFalse(any(loc["name"] == COMPLETION_LOCATION for loc in contract["locations"]))

    def test_shop_still_rejects_foreign_progression(self):
        foreign = ToMEItem("Foreign Progression", ItemClassification.progression, 1, 2)
        for loc in self.world.build.locations:
            if loc.event == "shop":
                self.assertFalse(self.world.get_location(loc.name).item_rule(foreign))


class TestTwoToMESlots(unittest.TestCase):
    def test_two_slot_fill_and_completion(self):
        multiworld = MultiWorld(2)
        multiworld.set_seed(20260918)
        multiworld.seed_name = "ToME two-slot regression"
        multiworld.game.update({1: ToMEWorld.game, 2: ToMEWorld.game})
        multiworld.player_name = {1: "ToME One", 2: "ToME Two"}
        args = Namespace()
        for name, option in ToMEWorld.options_dataclass.type_hints.items():
            setattr(args, name, {player: option.from_any(option.default) for player in (1, 2)})
        multiworld.set_options(args)
        multiworld.state = CollectionState(multiworld)
        for step in gen_steps:
            call_all(multiworld, step)
        distribute_items_restrictive(multiworld)
        self.assertTrue(multiworld.can_beat_game())
        self.assertTrue(multiworld.fulfills_accessibility())


class TestMixedWorldEarlyFill(unittest.TestCase):
    def test_requested_tome_ranks_can_land_in_another_game(self):
        options = dict(TestTightEarlyWindow.options)
        multiworld = setup_multiworld([ToMEWorld, TestWorld], seed=20260923,
                                      options=[options, {}])
        world = multiworld.worlds[1]
        target = CATALOG.items["talent:T_WEAPON_COMBAT"].name
        self.assertEqual(world.multiworld.early_items[1][target], 2)

        # AP's built-in test game supplies two reachable checks. Force the
        # requested Combat Accuracy copies across the world boundary while the
        # other ToME early ranks still use normal ToME early checks.
        host = Region("Menu", 2, multiworld)
        host.locations.extend(Location(2, f"Foreign Early {i}", 900_000 + i, host)
                              for i in range(2))
        multiworld.regions.append(host)
        multiworld.itempool.extend(Item(f"Foreign Filler {i}", ItemClassification.filler,
                                        900_000 + i, 2) for i in range(2))
        multiworld.completion_condition[2] = lambda state: True
        for loc in world.build.locations:
            if loc.early and loc.placement == "default":
                add_item_rule(multiworld.get_location(loc.name, 1),
                              lambda item: not (world._early_rules_active and
                                                item.player == 1 and item.name == target))
        for location in host.locations:
            add_item_rule(location, lambda item: item.player == 2 or
                          (item.player == 1 and item.name == target))

        distribute_items_restrictive(multiworld)
        assert_early_ranks_placed(self, multiworld, world)
        self.assertEqual({item.location.player for item in world._early_placed_ranks[target]}, {2})
        assert_remaining_mastery_copies_legal_late(self, multiworld, world)
