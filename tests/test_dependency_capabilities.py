from copy import deepcopy
from random import Random

import pytest

from tome_ap.catalog import Catalog, compile_catalog
from tome_ap.generation import Settings, _resolve_support_dependencies, create_build
from tome_ap.mailbox import validate_contract
from tome_ap.model import CATALOG_VERSION, CONTRACT_VERSION, ValidationError, digest
from .factories import fixture_export


def _profile_with_capabilities():
    export, profile = fixture_export(classes=4, generics=1)
    source = "fixture/class-0"
    preferred = "fixture/class-1"
    fallback = "fixture/class-2"
    anchor = "fixture/class-3"
    preferred_talent = export["trees"][1]["symbols"][0]
    fallback_talent = export["trees"][2]["symbols"][0]
    anchor_talent = export["trees"][3]["symbols"][0]
    profile.update(
        capabilities={
            "fixture_source": {
                "providers": [
                    {"tree": preferred, "talents": [preferred_talent]},
                    {"tree": fallback, "talents": [fallback_talent], "fallback": True},
                ]
            }
        },
        functional_dependencies={source: ["fixture_source"]},
        anchor_talents={anchor: [anchor_talent]},
    )
    return export, profile, source, preferred, fallback, anchor, preferred_talent, fallback_talent, anchor_talent


def test_catalog_v4_compiles_capabilities_and_anchors():
    export, profile, source, preferred, fallback, anchor, preferred_talent, fallback_talent, anchor_talent = _profile_with_capabilities()
    catalog = compile_catalog(export, profile)
    assert catalog.data["schema"] == CATALOG_VERSION == 4
    assert catalog.functional_dependencies[source] == ("fixture_source",)
    assert [p.tree for p in catalog.capability_providers["fixture_source"]] == [preferred, fallback]
    assert [p.fallback for p in catalog.capability_providers["fixture_source"]] == [False, True]
    assert catalog.anchor_talents[anchor] == (anchor_talent,)


def test_capability_prefers_already_ready_provider():
    export, profile, source, preferred, fallback, anchor, preferred_talent, fallback_talent, _ = _profile_with_capabilities()
    catalog = compile_catalog(export, profile)
    support, precollects = _resolve_support_dependencies(
        catalog, [source, preferred], [source, preferred]
    )
    assert fallback not in support
    assert preferred not in support
    assert "talent:" + preferred_talent in precollects
    assert "talent:" + fallback_talent not in precollects


def test_capability_uses_fallback_when_no_provider_is_ready():
    export, profile, source, preferred, fallback, anchor, preferred_talent, fallback_talent, _ = _profile_with_capabilities()
    catalog = compile_catalog(export, profile)
    support, precollects = _resolve_support_dependencies(catalog, [source], [source])
    assert support == [fallback]
    assert precollects == ["talent:" + fallback_talent]


def test_bonus_only_provider_is_promoted_to_support_before_it_counts_as_ready():
    export, profile, source, preferred, fallback, anchor, preferred_talent, fallback_talent, _ = _profile_with_capabilities()
    catalog = compile_catalog(export, profile)
    # preferred is present in the build but not ready at birth (analogous to a
    # prodigy-gated bonus tree). It must not satisfy the dependency silently.
    support, precollects = _resolve_support_dependencies(
        catalog, [source, preferred], [source]
    )
    assert fallback in support
    assert "talent:" + fallback_talent in precollects
    assert "talent:" + preferred_talent not in precollects


def test_anchor_precollects_once_and_does_not_add_a_tree():
    export, profile, source, preferred, fallback, anchor, preferred_talent, fallback_talent, anchor_talent = _profile_with_capabilities()
    catalog = compile_catalog(export, profile)
    support, precollects = _resolve_support_dependencies(catalog, [anchor], [anchor])
    assert support == []
    assert precollects == ["talent:" + anchor_talent]


def test_anchor_and_capability_precollect_dedupe_same_talent():
    export, profile = fixture_export(classes=2, generics=0)
    source = "fixture/class-0"
    provider = "fixture/class-1"
    talent = next(t["symbols"][0] for t in export["trees"] if t["key"] == provider)
    profile.update(
        capabilities={
            "fixture_source": {
                "providers": [{"tree": provider, "talents": [talent], "fallback": True}]
            }
        },
        functional_dependencies={source: ["fixture_source"]},
        anchor_talents={provider: [talent]},
    )
    catalog = compile_catalog(export, profile)
    support, precollects = _resolve_support_dependencies(catalog, [source], [source])
    assert support == [provider]
    assert precollects == ["talent:" + talent]


def test_capability_requires_exactly_one_fallback():
    export, profile, source, preferred, fallback, anchor, preferred_talent, fallback_talent, _ = _profile_with_capabilities()
    broken = deepcopy(profile)
    broken["capabilities"]["fixture_source"]["providers"][0]["fallback"] = True
    with pytest.raises(ValidationError, match="exactly one fallback"):
        compile_catalog(export, broken)



def test_capability_fallback_flag_must_be_boolean():
    export, profile, *_ = _profile_with_capabilities()
    broken = deepcopy(profile)
    broken["capabilities"]["fixture_source"]["providers"][1]["fallback"] = "yes"
    with pytest.raises(ValidationError, match="fallback flag must be boolean"):
        compile_catalog(export, broken)

def test_capability_provider_talent_must_belong_to_provider_tree():
    export, profile, source, preferred, fallback, anchor, preferred_talent, fallback_talent, _ = _profile_with_capabilities()
    broken = deepcopy(profile)
    broken["capabilities"]["fixture_source"]["providers"][1]["talents"] = [preferred_talent]
    with pytest.raises(ValidationError, match="runtime tree does not contain"):
        compile_catalog(export, broken)


def test_anchor_talent_must_belong_to_its_tree():
    export, profile, source, preferred, fallback, anchor, preferred_talent, fallback_talent, _ = _profile_with_capabilities()
    broken = deepcopy(profile)
    broken["anchor_talents"][anchor] = [preferred_talent]
    with pytest.raises(ValidationError, match="runtime tree does not contain"):
        compile_catalog(export, broken)


def test_contract_schema_stays_v3_and_hides_catalog_dependency_metadata():
    export, profile, source, preferred, fallback, anchor, preferred_talent, fallback_talent, _ = _profile_with_capabilities()
    # Make every class tree active so the generated build deterministically contains
    # both the dependent tree and an already-ready provider.
    catalog = compile_catalog(export, profile)
    build = create_build(
        catalog,
        Settings(
            class_tree_count=4,
            generic_tree_count=0,
            prodigy_count=0,
            starting_ranks=0,
            zone_exploration_checks=False,
            quest_checks="none",
            shop_checks="off",
        ),
        Random(1),
    )
    contract = build.contract(catalog)
    assert contract["schema"] == CONTRACT_VERSION == 3
    assert "capability_providers" not in contract
    assert "functional_dependencies" not in contract
    assert "anchor_talents" not in contract
    assert "talent:" + preferred_talent in contract["support_precollects"]


def test_old_catalog_schema_is_rejected_instead_of_silently_ignoring_v4_rules():
    export, profile, *_ = _profile_with_capabilities()
    catalog = compile_catalog(export, profile)
    old = deepcopy(catalog.data)
    old["schema"] = 3
    with pytest.raises(ValidationError, match="Unsupported catalog schema"):
        Catalog(old)


def test_contract_v3_accepts_a_legacy_catalog_hash_when_its_own_hash_is_valid():
    export, profile, *_ = _profile_with_capabilities()
    catalog = compile_catalog(export, profile)
    build = create_build(
        catalog,
        Settings(
            class_tree_count=4, generic_tree_count=0, prodigy_count=0, starting_ranks=0,
            zone_exploration_checks=False, quest_checks="none", shop_checks="off",
        ),
        Random(2),
    )
    contract = build.contract(catalog)
    body = {k: v for k, v in contract.items() if k != "contract_hash"}
    body["catalog_hash"] = "0" * 64  # stand-in for a valid pre-v4 catalog hash
    legacy = {**body, "contract_hash": digest(body)}
    assert validate_contract(legacy) == legacy
