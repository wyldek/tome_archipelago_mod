"""Run inside the pinned Archipelago checkout; these use real AP classes/fill."""
from argparse import Namespace
import unittest

from BaseClasses import CollectionState, ItemClassification, MultiWorld
from Fill import distribute_items_restrictive
from test.general import gen_steps
from worlds.AutoWorld import call_all

from .. import COMPLETION_EVENT, COMPLETION_LOCATION, ToMEItem, ToMEWorld
from .bases import ToMETestBase


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


class TestSmallWorld(ToMETestBase):
    options = {"class_tree_count": 2, "generic_tree_count": 2, "shop_checks": "off"}


class TestMinimalWorld(ToMETestBase):
    options = {"class_tree_count": 1, "generic_tree_count": 0, "prodigy_count": 0,
               "shop_checks": "off", "quest_checks": "none", "zone_exploration_checks": False}


class TestNoStarters(ToMETestBase):
    options = {"starting_ranks": 0}


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
