import json
from pathlib import Path


PROFILE = json.loads((Path(__file__).resolve().parents[1] / "profiles/wanderer-full.json").read_text(encoding="utf-8"))


def test_reviewed_functional_dependency_matrix_is_present():
    deps = PROFILE["functional_dependencies"]
    expected = {
        "cursed/advanced-shadowmancy": "shadow_source",
        "cursed/one-with-shadows": "shadow_source",
        "wild-gift/summon-advanced": "summon_source",
        "wild-gift/summon-augmentation": "summon_source",
        "chronomancy/spellbinding": "chronomancy_spell",
        "technique/finishing-moves": "combo_source",
        "spell/explosives": "alchemist_gem_source",
        "demented/beyond-sanity": "insanity_source",
        "demented/oblivion": "entropic_backlash_source",
        "spell/master-necromancer": "undead_minion_source",
        "spell/advanced-golemancy": "alchemy_golem_source",
    }
    assert {tree: caps[0] for tree, caps in deps.items()} == expected


def test_each_reviewed_capability_has_exactly_one_fallback():
    for capability, spec in PROFILE["capabilities"].items():
        providers = spec["providers"]
        assert providers
        assert sum(bool(p.get("fallback")) for p in providers) == 1, capability
        assert all(p.get("talents") for p in providers)


def test_known_implicit_anchors_are_predeclared():
    anchors = PROFILE["anchor_talents"]
    expected = {
        "cursed/shadows": "T_CALL_SHADOWS",
        "chronomancy/temporal-hounds": "T_TEMPORAL_HOUNDS",
        "psionic/thought-forms": "T_THOUGHT_FORMS",
        "chronomancy/speed-control": "T_TIME_DILATION",
        "spell/golemancy": "T_GOLEM_POWER",
        "spell/master-of-bones": "T_CALL_OF_THE_CRYPT",
        "spell/master-of-flesh": "T_CALL_OF_THE_MAUSOLEUM",
        "spell/dreadmaster": "T_DREAD",
        "demented/doom": "T_PROPHECY",
        "demented/friend-of-the-worm": "T_WORM_THAT_WALKS",
        "demented/madness": "T_DARK_WHISPERS",
        "demented/rift": "T_REALITY_FRACTURE",
        "demented/slow-death": "T_DIGEST",
        "demented/tentacles": "T_MUTATED_HAND",
        "demented/void": "T_VOID_STARS",
        "demented/chronophage": "T_ATROPHY",
        "demented/calamity": "T_JINXED_TOUCH",
        "demented/entropy": "T_ENTROPIC_GIFT",
    }
    assert {tree: talents[0] for tree, talents in anchors.items()} == expected


def test_old_insufficient_self_dependencies_were_removed():
    hard = PROFILE["support_dependencies"]
    assert "wild-gift/summon-advanced" not in hard
    assert "spell/advanced-golemancy" not in hard
    assert "chronomancy/temporal-hounds" not in hard
    assert "psionic/thought-forms" not in hard
    assert "chronomancy/speed-control" not in hard
