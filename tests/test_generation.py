from collections import Counter
from copy import deepcopy
from random import Random
import pytest
from tome_ap.catalog import Catalog, compile_catalog
from tome_ap.generation import Settings, create_build, allocate_level_rewards, subtract_copies
from tome_ap.locations import (
    PRIMARY_LOCATIONS, SHOP_LOCATION_COUNT, SHOP_LOCATIONS, BOSS_LOCATIONS,
    ZONE_LOCATIONS, QUEST_LOCATIONS, ZONE_QUEST_LOCATIONS, MAJOR_QUEST_LOCATIONS,
)
from tome_ap.model import ValidationError, level_location_id
from .factories import fixture_catalog, fixture_export

@pytest.mark.parametrize("classes,generics,expected", [
    (6,4,298),(9,6,398),(12,8,498),(4,2,218),(5,3,258)
])
def test_configurable_counts(classes, generics, expected):
    c = fixture_catalog()
    b = create_build(c, Settings(class_tree_count=classes, generic_tree_count=generics), Random(7))
    assert len(b.pool) == len(b.locations) == expected
    assert len(b.random_trees) == classes + generics
    assert "technique/combat-training" in b.mandatory_trees
    assert "technique/combat-training" not in b.random_trees
    assert sum(c.trees[k].kind == "class" for k in b.random_trees) == classes
    assert sum(c.trees[k].kind == "generic" for k in b.random_trees) == generics

@pytest.mark.parametrize("seed", range(20))
def test_all_generation_invariants(seed):
    c = fixture_catalog(); b = create_build(c, Settings(), Random(seed))
    assert len(set(b.prodigies)) == 5
    full = Counter(b.pool + b.precollected)
    for key in b.trees:
        for symbol in c.trees[key].symbols:
            assert full["talent:" + symbol] == c.items["talent:" + symbol].cap
    for stat in ("str","dex","con","mag","wil","cun"):
        assert full["stat:" + stat] == 10
    assert b.contract(c) == b.contract(c)
    assert len({l.code for l in b.locations}) == len(b.pool)
    assert {p.name for p in PRIMARY_LOCATIONS}.issubset({l.name for l in b.locations})

def test_deterministic_seed():
    c = fixture_catalog()
    assert create_build(c,Settings(),Random(456)).contract(c) == create_build(c,Settings(),Random(456)).contract(c)

def test_no_starters():
    b = create_build(fixture_catalog(), Settings(starting_ranks=0), Random(1))
    assert not b.starters and not b.support_precollects and len(b.pool) == 300

def test_actual_caps_not_assumed():
    e,p = fixture_export(classes=2,generics=2)
    e["talents"][0]["cap"] = 3
    c = compile_catalog(e,p)
    b = create_build(c,Settings(class_tree_count=2,generic_tree_count=2),Random(1))
    # 4 random trees (one 3-rank talent lowers 80 by 2) + 35 mandatory + 60 + 5 - 2 starters
    assert len(b.pool) == 176

def test_additional_talent_changes_budget():
    e,p = fixture_export(classes=2,generics=2)
    extra = "T_EXTRA"
    e["trees"][0]["symbols"].append(extra)
    e["talents"].append(dict(symbol=extra,name="Extra",cap=5,prodigy=False,mode="activated",hide=None,starter=True,resources=[]))
    c = compile_catalog(e,p)
    b = create_build(c,Settings(class_tree_count=2,generic_tree_count=2),Random(1))
    assert len(b.pool) in {178, 183}  # depends whether that class tree is sampled

def test_prodigy_bonus_tree_expands_pool():
    e,p = fixture_export(classes=2,generics=2)
    bonus="fixture/bonus-tree"
    syms=[f"T_BONUS_{i}" for i in range(4)]
    e["trees"].append(dict(key=bonus,name="Bonus",generic=False,symbols=syms,resources=[],allow_random=False,source="@vanilla@"))
    e["talents"].extend(dict(symbol=s,name=s,cap=5,prodigy=False,mode="activated",hide=None,starter=True,resources=[]) for s in syms)
    p["prodigy_rules"]={"T_FIXTURE_PRODIGY_0":{"bonus_trees":[bonus]}}
    c=compile_catalog(e,p)
    # Pick all prodigies so the rule is guaranteed selected.
    b=create_build(c,Settings(class_tree_count=2,generic_tree_count=2,prodigy_count=12),Random(3))
    assert bonus in b.bonus_trees
    assert sum(1 for x in b.pool+b.precollected if x.startswith("talent:T_BONUS_"))==20

@pytest.mark.parametrize("bad",[True,0,21,-1,2.5,"6"])
def test_reject_invalid_class_counts(bad):
    with pytest.raises(ValidationError): Settings(class_tree_count=bad).validate()

def test_too_few_eligible_trees():
    with pytest.raises(ValidationError): create_build(fixture_catalog(3,3),Settings(),Random(1))

def test_prodigy_shortage():
    with pytest.raises(ValidationError): create_build(fixture_catalog(),Settings(prodigy_count=13),Random(1))

def test_location_reservation():
    ids=[level_location_id(l,r) for l in range(2,51) for r in range(1,65)]
    assert len(ids)==len(set(ids))
    with pytest.raises(ValidationError): level_location_id(3,65)

def test_allocator_exact():
    schedule=allocate_level_rewards(280,tuple(range(2,41)))
    assert sum(schedule.values())==280
    assert max(schedule.values())-min(schedule.values())<=1

def test_allocator_capacity_and_sparse_schedule():
    with pytest.raises(ValidationError): allocate_level_rewards(10000,(2,3))
    sparse = allocate_level_rewards(1,(2,3))
    assert sparse == {2: 1, 3: 0}
    spread = allocate_level_rewards(3, tuple(range(2, 11)))
    assert sum(spread.values()) == 3
    assert spread[2] == 1 and spread[10] == 1

def test_missing_starter_rejected():
    with pytest.raises(ValidationError): subtract_copies(["A"],["B"])

def test_only_one_copy_removed():
    assert subtract_copies(["A"]*5,["A"])==["A"]*4

def test_collision_rejected():
    data=deepcopy(fixture_catalog().data)
    data["items"][1]["code"]=data["items"][0]["code"]
    with pytest.raises(ValidationError): Catalog(data)


def _add_support_tree(e, key="fixture/support", symbols=("T_SUPPORT_ENABLE", "T_SUPPORT_2")):
    e["trees"].append(dict(
        key=key, name="Support", generic=True, symbols=list(symbols), resources=[],
        allow_random=False, source="@vanilla@",
    ))
    e["talents"].extend(dict(
        symbol=s, name=s, cap=5, prodigy=False, mode="passive", hide=None,
        starter=False, resources=[],
    ) for s in symbols)


def test_cross_tree_support_dependency_adds_tree_and_one_free_rank():
    e,p = fixture_export(classes=2,generics=2)
    source=e["player_trees"][0]
    _add_support_tree(e)
    p["support_dependencies"]={source:[{"tree":"fixture/support","talents":["T_SUPPORT_ENABLE"]}]}
    c=compile_catalog(e,p)
    # Force every class tree to be selected so source is active.
    b=create_build(c,Settings(class_tree_count=2,generic_tree_count=0,prodigy_count=0,starting_ranks=0, zone_exploration_checks=False, quest_checks="none", shop_checks="off"),Random(1))
    assert "fixture/support" in b.support_trees
    assert b.support_precollects == ["talent:T_SUPPORT_ENABLE"]
    full=Counter(b.pool+b.precollected)
    assert full["talent:T_SUPPORT_ENABLE"]==5
    assert b.pool.count("talent:T_SUPPORT_ENABLE")==4


def test_same_tree_support_dependency_precollects_without_duplicate_tree():
    e,p = fixture_export(classes=1,generics=0)
    source=e["player_trees"][0]
    enable=e["trees"][0]["symbols"][0]
    p["support_dependencies"]={source:[{"tree":source,"talents":[enable]}]}
    c=compile_catalog(e,p)
    b=create_build(c,Settings(class_tree_count=1,generic_tree_count=0,prodigy_count=0,starting_ranks=0, zone_exploration_checks=False, quest_checks="none", shop_checks="off"),Random(2))
    assert b.support_trees == []
    assert b.support_precollects == ["talent:"+enable]
    assert b.pool.count("talent:"+enable)==4


def test_support_dependencies_resolve_transitively_and_dedupe_free_rank():
    e,p = fixture_export(classes=1,generics=0)
    source=e["player_trees"][0]
    _add_support_tree(e,"fixture/support-a",("T_SUPPORT_A","T_SUPPORT_SHARED"))
    _add_support_tree(e,"fixture/support-b",("T_SUPPORT_B","T_SUPPORT_B2"))
    p["support_dependencies"]={
        source:[{"tree":"fixture/support-a","talents":["T_SUPPORT_A"]}],
        "fixture/support-a":[
            {"tree":"fixture/support-b","talents":["T_SUPPORT_B"]},
            {"tree":"fixture/support-a","talents":["T_SUPPORT_A"]},
        ],
    }
    c=compile_catalog(e,p)
    b=create_build(c,Settings(class_tree_count=1,generic_tree_count=0,prodigy_count=0,starting_ranks=0, zone_exploration_checks=False, quest_checks="none", shop_checks="off"),Random(3))
    assert b.support_trees == ["fixture/support-a","fixture/support-b"]
    assert b.support_precollects.count("talent:T_SUPPORT_A")==1
    assert "talent:T_SUPPORT_B" in b.support_precollects


def test_bad_support_dependency_rejected():
    e,p = fixture_export(classes=1,generics=0)
    source=e["player_trees"][0]
    p["support_dependencies"]={source:[{"tree":source,"talents":["T_NOT_IN_TREE"]}]}
    with pytest.raises(ValidationError):
        compile_catalog(e,p)


def test_world_location_classes_and_early_band():
    assert len(SHOP_LOCATIONS) == SHOP_LOCATION_COUNT == 126
    assert all(loc.placement == "non_progression" and not loc.early for loc in SHOP_LOCATIONS)
    priority = [loc for loc in BOSS_LOCATIONS if loc.placement == "priority"]
    assert len(priority) == 10
    assert all(loc.early for loc in priority)
    assert len([loc for loc in ZONE_LOCATIONS if loc.early]) == 10
    assert len(ZONE_QUEST_LOCATIONS) == 4
    assert all(loc.early for loc in ZONE_QUEST_LOCATIONS)
    assert len(MAJOR_QUEST_LOCATIONS) == 7


def test_default_shop_checks_replace_level_checks_without_filler():
    c = fixture_catalog()
    b = create_build(c, Settings(), Random(9))
    assert b.pool.count("vitality") == 0
    assert len(b.pool) == len(b.locations) == 298
    assert sum(loc.event == "shop" for loc in b.locations) == 126
    assert sum(loc.event == "level" for loc in b.locations) == 126
    assert all(loc.placement == "non_progression" for loc in b.locations if loc.event == "shop")


def test_location_options_rebalance_level_budget():
    c = fixture_catalog()
    default = create_build(c, Settings(), Random(9))
    no_shops = create_build(c, Settings(shop_checks="off"), Random(9))
    one_shop = create_build(c, Settings(shop_checks_per_store=1), Random(9))
    major_quests = create_build(c, Settings(quest_checks="major"), Random(9))
    no_quests = create_build(c, Settings(quest_checks="none"), Random(9))
    no_zones = create_build(c, Settings(zone_exploration_checks=False), Random(9))

    assert sum(l.event == "shop" for l in default.locations) == 126
    assert sum(l.event == "shop" for l in no_shops.locations) == 0
    assert sum(l.event == "shop" for l in one_shop.locations) == 42
    assert sum(l.event == "quest" for l in major_quests.locations) == 7
    assert sum(l.event == "quest" for l in no_quests.locations) == 0
    assert sum(l.event == "zone" for l in no_zones.locations) == 0
    assert sum(l.event == "level" for l in no_shops.locations) == sum(l.event == "level" for l in default.locations) + 126
    assert sum(l.event == "level" for l in one_shop.locations) == sum(l.event == "level" for l in default.locations) + 84
    assert sum(l.event == "level" for l in major_quests.locations) == sum(l.event == "level" for l in default.locations) + 4
    assert sum(l.event == "level" for l in no_quests.locations) == sum(l.event == "level" for l in default.locations) + 11
    assert sum(l.event == "level" for l in no_zones.locations) == sum(l.event == "level" for l in default.locations) + 18


def test_early_level_cutoff_and_boss_priority_options():
    c = fixture_catalog()
    b = create_build(c, Settings(early_level_max=6, t1_t2_boss_priority=False), Random(5))
    assert all(l.early for l in b.locations if l.event == "level" and l.level <= 6)
    assert not any(l.early for l in b.locations if l.event == "level" and l.level > 6)
    early_bosses = [l for l in b.locations if l.event == "boss" and l.early]
    assert len(early_bosses) == 10
    assert all(l.placement == "default" for l in early_bosses)


def test_early_window_has_minimum_and_extends_only_for_required_ranks():
    with pytest.raises(ValidationError, match="early_level_max"):
        Settings(early_level_max=2).validate()

    export, profile = fixture_export(classes=1, generics=0)
    combat = next(t for t in export["trees"] if t["key"] == "technique/combat-training")
    profile["anchor_talents"] = {
        combat["key"]: [sym for sym in combat["symbols"] for _ in range(5)]
    }
    catalog = compile_catalog(export, profile)
    settings = Settings(
        class_tree_count=1, generic_tree_count=0, prodigy_count=0,
        starting_ranks=0, level_ceiling=50, zone_exploration_checks=False,
        quest_checks="none", shop_checks="off", early_level_max=3,
    )
    build = create_build(catalog, settings, Random(1))
    assert len(build.early_talents) == 35
    assert sum(loc.early for loc in build.locations) >= len(build.early_talents)
    assert max(loc.level for loc in build.locations if loc.event == "level" and loc.early) > 3
    assert all(loc.early for loc in build.locations if loc.event == "level" and loc.level <= 3)


def test_early_window_rejects_an_impossible_non_shop_budget():
    export, profile = fixture_export(classes=3, generics=0)
    combat = next(t for t in export["trees"] if t["key"] == "technique/combat-training")
    profile["anchor_talents"] = {
        combat["key"]: [sym for sym in combat["symbols"] for _ in range(5)]
    }
    catalog = compile_catalog(export, profile)
    with pytest.raises(ValidationError, match="Only .* non-shop ToME checks"):
        create_build(catalog, Settings(
            class_tree_count=3, generic_tree_count=0, prodigy_count=0,
            starting_ranks=0, level_ceiling=50, zone_exploration_checks=False,
            quest_checks="none", shop_checks="non_progression",
            shop_checks_per_store=3, early_level_max=3,
        ), Random(1))


def test_too_many_fixed_checks_for_tiny_build_rejected_cleanly():
    c = fixture_catalog()
    with pytest.raises(ValidationError, match="Enabled fixed checks"):
        create_build(c, Settings(class_tree_count=1, generic_tree_count=0, prodigy_count=0, starting_ranks=0), Random(1))
