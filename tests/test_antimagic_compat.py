from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTOR = (ROOT / "addon/tome-archipelago/superload/mod/class/Actor.lua").read_text(encoding="utf-8")
AP = (ROOT / "addon/tome-archipelago/overload/mod/class/Archipelago.lua").read_text(encoding="utf-8")

def test_ap_actor_suppresses_vanilla_power_exclusion_flags():
    assert 'prop=="forbid_arcane" or prop=="has_arcane_knowledge"' in ACTOR
    assert 'AP.isCharacter(self)' in ACTOR
    assert 'return old_attr(self,prop,v,fix)' in ACTOR

def test_ap_initialization_scrubs_preexisting_power_flags():
    assert 'actor.forbid_arcane=nil' in AP
    assert 'actor.has_arcane_knowledge=nil' in AP
