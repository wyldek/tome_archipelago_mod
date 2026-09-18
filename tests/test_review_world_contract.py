"""Execute real APWorld method bodies with small AP API doubles.

These fast tests cover our contract/logic wiring, NOT Archipelago's fill solver.
The native tests in apworld/tome/test/test_world.py remain a release gate.
"""
import ast
from collections import Counter, defaultdict
from enum import IntFlag
from pathlib import Path
from random import Random
from types import SimpleNamespace

import pytest

from tome_ap.generation import Settings, create_build
from tome_ap.locations import PRIMARY_NAME_TO_ID
from tome_ap.model import GAME, LEVEL_ID_STRIDE, level_location_id
from .factories import fixture_catalog


class Classification(IntFlag):
    filler = 0
    progression = 1
    useful = 2


class ItemDouble:
    def __init__(self, name, classification, code, player):
        self.name, self.classification, self.code, self.player = name, classification, code, player
        self.location = None

    @property
    def advancement(self):
        return bool(self.classification & Classification.progression)


class LocationDouble:
    def __init__(self, player, name, address, parent):
        self.player, self.name, self.address, self.parent_region = player, name, address, parent
        self.item = None
        self.locked = False
        self.access_rule = lambda state: True
        self.item_rule = lambda item: True

    def can_reach(self, state):
        return self.access_rule(state)

    def place_locked_item(self, item):
        self.item, self.locked, item.location = item, True, self


class RegionDouble:
    def __init__(self, name, player, multiworld):
        self.name, self.player, self.multiworld, self.locations = name, player, multiworld, []

    def connect(self, other):
        pass


class WorldDouble:
    def get_location(self, name):
        return next(loc for region in self.multiworld.regions for loc in region.locations if loc.name == name)


class StateDouble:
    def __init__(self):
        self.items = Counter()
        self.locations_checked = set()

    def has(self, name, player):
        return self.items[name, player] > 0

    def sweep(self, locations):
        # The important upstream semantic: useful/filler locations are not swept.
        while True:
            found = [loc for loc in locations if loc.item and loc.item.advancement
                     and loc not in self.locations_checked and loc.can_reach(self)]
            if not found:
                return
            for loc in found:
                self.items[loc.item.name, loc.item.player] += 1
                self.locations_checked.add(loc)


def add_rule(location, rule):
    previous = location.item_rule
    location.item_rule = lambda item: previous(item) and rule(item)


@pytest.fixture
def world():
    catalog = fixture_catalog()
    namespace = dict(CATALOG=catalog, GAME=GAME, Settings=Settings, create_build=create_build,
                     LEVEL_ID_STRIDE=LEVEL_ID_STRIDE, level_location_id=level_location_id,
                     PRIMARY_NAME_TO_ID=PRIMARY_NAME_TO_ID, Item=ItemDouble, Location=LocationDouble,
                     Region=RegionDouble, World=WorldDouble, ItemClassification=Classification,
                     LocationProgressType=SimpleNamespace(PRIORITY="priority"), ToMEWeb=lambda: None,
                     ToMEOptions=object, add_item_rule=add_rule)
    source = Path(__file__).resolve().parents[1] / "apworld/tome/__init__.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    nodes = [node for node in module.body if (
        isinstance(node, ast.ClassDef) and node.name in {"ToMEItem", "ToMELocation", "ToMEWorld"}
    ) or (
        isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id.startswith("COMPLETION_")
                                           for t in node.targets)
    )]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), namespace)
    instance = namespace["ToMEWorld"]()
    instance.player = 1
    instance.multiworld = SimpleNamespace(regions=[], completion_condition={},
        early_items=defaultdict(Counter), local_early_items=defaultdict(Counter), itempool=[])
    instance.build = create_build(catalog, Settings(), Random(4))
    instance.create_regions()
    instance.set_rules()
    return instance, namespace


@pytest.mark.parametrize("kind", [Classification.filler, Classification.useful, Classification.progression])
def test_victory_reward_classification_does_not_control_completion(world, kind):
    instance, namespace = world
    victory = instance.get_location("Age of Ascendancy — Victory")
    victory.place_locked_item(ItemDouble("arbitrary reward", kind, 1, 1))
    state = StateDouble()
    locations = [loc for region in instance.multiworld.regions for loc in region.locations]
    state.sweep(locations)
    assert instance.multiworld.completion_condition[1](state)
    if kind != Classification.progression:
        assert victory not in state.locations_checked


def test_completion_tracks_victory_access_without_networking_an_event(world):
    instance, namespace = world
    event = instance.get_location(namespace["COMPLETION_LOCATION"])
    victory = instance.get_location("Age of Ascendancy — Victory")
    assert event.address is None and event.item.code is None and event.locked
    assert event.name not in instance.location_name_to_id
    assert event.item.name not in instance.item_name_to_id
    assert len(instance.build.pool) == len(instance.fill_slot_data()["locations"])
    locations = [loc for region in instance.multiworld.regions for loc in region.locations]
    assert len(locations) == len(instance.build.pool) + 1
    victory.access_rule = lambda state: False
    state = StateDouble(); state.sweep(locations)
    assert not instance.multiworld.completion_condition[1](state)
    victory.access_rule = lambda state: True
    state.sweep(locations)
    assert instance.multiworld.completion_condition[1](state)


def test_all_shuffled_rewards_remain_non_progression_and_shops_reject_foreign_progression(world):
    instance, namespace = world
    catalog = namespace["CATALOG"]
    for key in instance.build.pool:
        assert not instance.create_item(catalog.items[key].name).advancement
    foreign = ItemDouble("foreign progression", Classification.progression, 1, 2)
    for location in instance.build.locations:
        if location.event == "shop":
            assert not instance.get_location(location.name).item_rule(foreign)
