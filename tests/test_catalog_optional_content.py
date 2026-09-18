"""Optional policies cannot make absent/excluded DLC categories mandatory."""
from copy import deepcopy
from random import Random

import pytest

from tome_ap.catalog import compile_catalog
from tome_ap.generation import Settings, create_build
from tome_ap.model import ValidationError
from .factories import fixture_export


@pytest.mark.parametrize("field", ["bonus_trees", "choose_one", "cleanup_trees"])
def test_missing_prodigy_does_not_require_its_optional_categories(field):
    export, profile = fixture_export()
    baseline = compile_catalog(export, profile)
    profile["prodigy_rules"]["T_NOT_INSTALLED"] = {field: ["dlc/not-installed"]}
    profile["support_dependencies"]["dlc/not-installed"] = [
        {"tree": "dlc/also-not-installed", "talents": ["T_NOT_INSTALLED_HELPER"]}
    ]
    result = compile_catalog(export, profile)
    assert result.hash == baseline.hash
    assert "dlc/not-installed" not in result.trees


@pytest.mark.parametrize("field", ["bonus_trees", "choose_one", "cleanup_trees"])
def test_excluded_prodigy_does_not_require_missing_category(field):
    export, profile = fixture_export()
    profile["exclude_prodigies"] = ["T_FIXTURE_PRODIGY_0"]
    baseline = compile_catalog(export, profile)
    profile["prodigy_rules"]["T_FIXTURE_PRODIGY_0"] = {field: ["dlc/not-installed"]}
    assert compile_catalog(export, profile).hash == baseline.hash


def test_installed_prodigy_still_requires_its_categories():
    export, profile = fixture_export()
    profile["prodigy_rules"]["T_FIXTURE_PRODIGY_0"] = {"bonus_trees": ["dlc/not-installed"]}
    with pytest.raises(ValidationError, match="missing required AP trees: dlc/not-installed"):
        compile_catalog(export, profile)


def test_installed_bonus_and_transitive_support_still_compile():
    export, profile = fixture_export()
    # Existing categories made bonus-only, so this exercises the closure rather
    # than succeeding merely because every required tree was already a player tree.
    export["player_trees"].remove("fixture/class-0")
    export["player_trees"].remove("fixture/class-1")
    profile["prodigy_rules"]["T_FIXTURE_PRODIGY_0"] = {"bonus_trees": ["fixture/class-0"]}
    profile["support_dependencies"]["fixture/class-0"] = [
        {"tree": "fixture/class-1", "talents": ["T_FIXTURE_CLASS_1_0"]}
    ]
    catalog = compile_catalog(export, profile)
    assert "fixture/class-0" in catalog.trees
    assert "fixture/class-1" in catalog.trees
    assert catalog.support_dependencies["fixture/class-0"][0].required_tree == "fixture/class-1"
    build = create_build(catalog, Settings(prodigy_count=12), Random(2))
    assert "fixture/class-1" in build.support_trees
    assert "talent:T_FIXTURE_CLASS_1_0" in build.precollected
    assert len(build.pool) == len(build.locations)


@pytest.mark.parametrize("seed", range(20))
def test_ignored_optional_policy_preserves_existing_seed_contract(seed):
    export, profile = fixture_export()
    before = compile_catalog(export, profile)
    profile["prodigy_rules"]["T_NOT_INSTALLED"] = {"bonus_trees": ["dlc/not-installed"]}
    after = compile_catalog(export, profile)
    assert create_build(before, Settings(), Random(seed)).contract(before) == (
        create_build(after, Settings(), Random(seed)).contract(after)
    )
