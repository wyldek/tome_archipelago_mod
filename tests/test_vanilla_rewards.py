from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTOR = (ROOT / "addon/tome-archipelago/superload/mod/class/Actor.lua").read_text(encoding="utf-8")
AP = (ROOT / "addon/tome-archipelago/overload/mod/class/Archipelago.lua").read_text(encoding="utf-8")
HOOKS = (ROOT / "addon/tome-archipelago/hooks/load.lua").read_text(encoding="utf-8")

def test_direct_stat_changes_are_not_blocked():
    assert "local old_incstat=_M.incStat" not in ACTOR
    assert "Direct permanent core-stat changes from vanilla content remain legal" in ACTOR

def test_free_point_pools_are_scrubbed_every_poll_pass():
    assert 'POINT_FIELDS={"unused_talents","unused_generics","unused_stats","unused_talents_types","unused_prodigies"}' in AP
    poll = AP.split("function M.poll(g)", 1)[1]
    assert "M.zeroPointPools(actor)" in poll.split("M.tick_count=M.tick_count+1", 1)[0]

def test_native_category_and_mastery_rewards_are_blocked():
    assert "old_learn_type=_M.learnTalentType" in ACTOR
    assert "blocked_native_categories" in ACTOR
    assert "old_set_mastery=_M.setTalentTypeMastery" in ACTOR
    assert "blocked_native_mastery" in ACTOR

def test_escort_rewards_keep_only_core_stats():
    assert 'class:bindHook("Quest:escort:reward"' in HOOKS
    body = HOOKS.split('class:bindHook("Quest:escort:reward"', 1)[1]
    assert "out.stats=src.stats" in body
    assert "out.talents" not in body
    assert "out.types" not in body
    assert "out.saves" not in body

def test_ap_stat_packages_stack_with_vanilla_direct_bonuses():
    assert "actor:incStat(id,item.amount)" in AP
    assert "60-current" not in AP
