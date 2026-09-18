"""Behavioral tests of the complete addon against the shared fake ToME engine."""
import json
from pathlib import Path
from random import Random

import pytest

from tome_ap.generation import Settings, create_build
from tome_ap.model import Identity, Receipt
from ._lua_exec import LuaExecutor
from .factories import fixture_catalog

ROOT = Path(__file__).resolve().parents[1]
LUA = ROOT / "addon/tome-archipelago/overload/mod/class"


def lua_text(value):
    # JSON is transported as data, not interpolated executable Lua. Long-string
    # delimiters are selected so even adversarial input cannot close the string.
    eq = "="
    while "]" + eq + "]" in value:
        eq += "="
    return "[" + eq + "[" + value + "]" + eq + "]"


@pytest.fixture
def engine():
    vm = LuaExecutor()
    catalog = fixture_catalog()
    build = create_build(catalog, Settings(), Random(4))
    contract = build.contract(catalog)
    primary = catalog.items[build.starters[0]]
    snapshot = dict(protocol=1, complete=True, contract=contract,
                    identity=Identity("Lua test", 0, 1, contract["contract_hash"]).to_dict(),
                    receipts=[Receipt(primary.code).to_dict()] * 2,
                    checked_locations=[], scouted_locations=[], revision=1, connected=True)
    vm.execute("JSON=(function()\n" + (LUA / "ArchipelagoJSON.lua").read_text(encoding="utf-8") + "\nend)()")
    vm.execute('package.preload["mod.class.ArchipelagoJSON"]=function()return JSON end')
    vm.execute("AP=(function()\n" + (LUA / "Archipelago.lua").read_text(encoding="utf-8") + "\nend)()")
    vm.execute('package.preload["mod.class.Archipelago"]=function()return AP end')
    vm.execute("snapshot=JSON.decode(" + lua_text(json.dumps(snapshot)) + ")")
    vm.execute((ROOT / "tests/lua/engine.lua").read_text(encoding="utf-8"))
    vm.execute("primary=" + lua_text(primary.symbol))
    extra = next(i for i in catalog.items.values() if i.kind == "talent" and i.tree not in build.trees)
    vm.execute("extra=JSON.decode(" + lua_text(json.dumps(extra.to_dict())) + ")")
    try:
        yield vm
    finally:
        vm.close()


def test_complete_initialization_and_exact_receipts(engine):
    engine.execute('''
      poll(); assert(not AP.last_error, tostring(AP.last_error))
      assert(actor:getTalentLevelRaw(primary)==2)
      assert(actor.archipelago_state.applied_count==2)
      assert(actor.stats[1]==10 and actor.unused_talents==0)
      assert(actor:getTalentLevelRaw("T_SHOOT")==1 and actor:getTalentLevelRaw("T_RELOAD")==1)
      for i=1,10 do poll() end
      assert(actor:getTalentLevelRaw(primary)==2)
    ''')


@pytest.mark.parametrize("resource,maximum", [("mana",100),("stamina",100),("psi",100),
    ("vim",100),("positive",100),("negative",100),("hate",100),("feedback",100),
    ("steam",100),("soul",6),("equilibrium",100),("paradox",100)])
def test_display_poll_never_refills_or_rewrites_regeneration(engine, resource, maximum):
    engine.execute(f'''
      snapshot.contract.trees[1].resources=JSON.array({{{lua_text(resource)}}})
      publish_snapshot(); poll(); assert(not AP.last_error, tostring(AP.last_error))
      actor[ {lua_text(resource)} ]=3
      actor[ {lua_text(resource+'_regen')} ]=-7
      actor[ {lua_text('max_'+resource)} ]={maximum}
      local learns=actor.category_learns
      for i=1,30 do poll() end
      assert(not AP.last_error, tostring(AP.last_error))
      assert(actor[ {lua_text(resource)} ]==3, "idle refill")
      assert(actor[ {lua_text(resource+'_regen')} ]==-7, "idle regen rewrite")
      assert(actor[ {lua_text('max_'+resource)} ]=={maximum})
      assert(actor.category_learns==learns, "known categories relearned")
    ''')


def test_legacy_save_adopts_resource_flags_without_refill(engine):
    engine.execute('''
      poll(); actor.mana=2; actor.stamina=4; actor.mana_regen=-3
      local s=actor.archipelago_state
      local cursor=s.applied_count
      s.resources_initialized=nil
      poll(); assert(not AP.last_error, tostring(AP.last_error))
      assert(actor.mana==2 and actor.stamina==4 and actor.mana_regen==-3)
      assert(s.resources_initialized.mana and s.resources_initialized.stamina)
      assert(s.applied_count==cursor)
    ''')


def test_unselected_admin_talent_is_granted_once_and_survives_reconciliation(engine):
    engine.execute('''
      poll(); local s=actor.archipelago_state
      assert(not s.tree_defs[extra.tree]); actor.mana=2
      snapshot.receipts[#snapshot.receipts+1]={item=extra.code}; publish_snapshot(); poll()
      assert(not AP.last_error, tostring(AP.last_error))
      assert(s.extra_trees[extra.tree] and s.tree_defs[extra.tree])
      assert(actor:knowTalentType(extra.tree))
      assert(actor:getTalentLevelRaw(extra.symbol)==1 and s.applied_count==3)
      assert(actor.mana==2, "new category refilled an existing resource")
      for i=1,5 do poll() end
      assert(actor:getTalentLevelRaw(extra.symbol)==1)
      snapshot.receipts[#snapshot.receipts+1]={item=extra.code}; publish_snapshot(); poll()
      assert(actor:getTalentLevelRaw(extra.symbol)==2 and s.applied_count==4)
    ''')


def test_new_admin_resource_is_initialized_only_once(engine):
    engine.execute('''
      poll(); actor.definitions[extra.symbol].psi=1
      snapshot.receipts[#snapshot.receipts+1]={item=extra.code}; publish_snapshot(); poll()
      assert(not AP.last_error, tostring(AP.last_error))
      assert(actor.archipelago_state.resources_initialized.psi)
      assert(actor.psi==50)
      actor.psi=1; poll(); assert(actor.psi==1)
    ''')


def test_unselected_missing_content_does_not_block_birth(engine):
    engine.execute('''
      actor[extra.symbol]=nil; actor.definitions[extra.symbol]=nil
      poll(); assert(not AP.last_error, tostring(AP.last_error))
      assert(actor.archipelago_state.applied_count==2)
    ''')


def test_missing_selected_content_fails_before_binding(engine):
    engine.execute('''
      actor[primary]=nil
      poll(); assert(AP.last_error and AP.last_error:find("Unavailable talent constant",1,true))
      assert(actor.archipelago_state==nil)
      assert(actor.stats[1]==12)
    ''')


def test_unavailable_admin_member_fails_before_category_or_resource_mutation(engine):
    engine.execute('''
      poll(); local s=actor.archipelago_state
      actor[extra.symbol]=nil; actor.definitions[extra.symbol]=nil
      actor.mana=2; local learns=actor.category_learns
      snapshot.receipts[#snapshot.receipts+1]={item=extra.code}; publish_snapshot(); poll()
      assert(s.error and s.error:find("Unavailable talent",1,true))
      assert(s.applied_count==2 and not s.extra_trees[extra.tree])
      assert(not actor:knowTalentType(extra.tree) and not s.tree_defs[extra.tree])
      assert(actor.mana==2 and actor.category_learns==learns)
      poll(); assert(s.applied_count==2)
    ''')


def test_prefix_change_and_native_goal_remain_distinct(engine):
    engine.execute('''
      poll(); assert(not actor.archipelago_state.goal)
      snapshot.receipts[1].item=extra.code; publish_snapshot(); poll()
      assert(AP.last_error:find("prefix changed",1,true))
      assert(actor.archipelago_state.applied_count==2)
      assert(not actor.archipelago_state.goal)
    ''')


def test_native_victory_still_required_for_game_goal(engine):
    engine.execute('''
      poll(); local s=actor.archipelago_state
      assert(not s.goal)
      actor.winner="full"; poll(); assert(s.goal and s.checks["790000"])
      for key,loc in pairs(s.locations) do
        if loc.event=="level" then assert(s.checks[key]) end
        if loc.event=="shop" or loc.event=="boss" then assert(not s.checks[key]) end
      end
    ''')


def test_failed_native_callback_is_not_retried(engine):
    engine.execute('''
      AP.initialize(game,snapshot)
      actor.learnTalent=function(self,id,force,n) self.raw[id]=1; error("simulated engine failure") end
      poll(); local s=actor.archipelago_state
      assert(s.error and s.error:find("simulated engine failure",1,true))
      assert(s.applied_count==0 and actor.raw[primary]==1)
      poll(); assert(s.applied_count==0 and actor.raw[primary]==1)
    ''')
