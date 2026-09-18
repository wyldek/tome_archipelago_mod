from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AP = (ROOT / "addon/tome-archipelago/overload/mod/class/Archipelago.lua").read_text(encoding="utf-8")

def test_shoot_and_reload_are_baseline_ap_utilities():
    assert 'BASELINE_UTILITY_TALENTS={"T_SHOOT","T_RELOAD"}' in AP
    assert 'enableBaselineUtilities(actor)' in AP
    assert 'actor:learnTalent(tid,true,1)' in AP

def test_shoot_is_default_ranged_click_action():
    assert 'actor.auto_shoot_talent=actor.T_SHOOT' in AP

def test_attack_is_not_reimplemented_as_ap_progression():
    assert '"T_ATTACK"' not in AP.split('BASELINE_UTILITY_TALENTS=', 1)[1].split('}', 1)[0]
