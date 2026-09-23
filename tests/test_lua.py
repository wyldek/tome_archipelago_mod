"""Execute the real Lua addon against a fake engine, not a real ToME process."""
from pathlib import Path
from random import Random
import json
import pytest
lupa=pytest.importorskip("lupa",reason="Optional lupa package is needed for Lua execution tests")
from tome_ap.generation import Settings,create_build
from tome_ap.model import Identity,Receipt
from tome_ap.mailbox import client_snapshot
from .factories import fixture_catalog
ROOT=Path(__file__).resolve().parents[1]
LUA=ROOT/"addon/tome-archipelago"

def runtime():
    vm=lupa.LuaRuntime(unpack_returned_tuples=True)
    vm.execute("unpack = unpack or table.unpack")
    codec=vm.execute((LUA/"overload/mod/class/ArchipelagoJSON.lua").read_text(encoding="utf-8"))
    vm.globals().JSON=codec
    vm.execute('package.preload["mod.class.ArchipelagoJSON"]=function() return JSON end')
    return vm,codec

@pytest.mark.parametrize("value",[{},[],[1,2,3],{"hello":"Maj’Eyal"},{"control":"\n\r\t\u0001"},{"x":True,"y":False,"z":None},{"unicode":"😀"},1.25,-1250])
def test_json_round_trip(value):
    vm,codec=runtime()
    assert json.loads(codec.encode(codec.decode(json.dumps(value,ensure_ascii=True))))==value

@pytest.mark.parametrize("text",['{"x":1,"x":2}','[1,]','{"x":}','"\\uD800"','01','1.','1.e3','NaN','true false'])
def test_json_rejects_invalid(text):
    vm,codec=runtime()
    with pytest.raises(lupa.LuaError):codec.decode(text)

def engine(receipts_count=2):
    vm,codec=runtime()
    ap=vm.execute((LUA/"overload/mod/class/Archipelago.lua").read_text(encoding="utf-8"))
    vm.globals().AP=ap
    vm.execute('package.preload["mod.class.Archipelago"]=function() return AP end')
    catalog=fixture_catalog();build=create_build(catalog,Settings(),Random(4));contract=build.contract(catalog)
    identity=Identity("Lua test",0,1,contract["contract_hash"])
    primary=catalog.items[build.starters[0]]
    receipts=[Receipt(primary.code)]*receipts_count
    snapshot=client_snapshot(identity,contract,receipts,set(),1,True)
    vm.globals().snapshot=codec.decode(json.dumps(snapshot))
    vm.execute((ROOT/"tests/lua/engine.lua").read_text(encoding="utf-8"))
    return vm,codec,ap,catalog,build,primary

def test_lua_grants_and_point_pools():
    vm,codec,ap,c,b,item=engine()
    vm.globals().poll();actor=vm.globals().actor
    assert actor.raw[actor[item.symbol]]==2
    assert actor.archipelago_state.applied_count==2
    assert actor.unused_talents==actor.unused_generics==actor.unused_stats==actor.unused_prodigies==0
    assert actor.stats[1]==10
    vm.globals().poll()
    assert actor.raw[actor[item.symbol]]==2

def test_lua_overcap_receipts_advance():
    vm,codec,ap,c,b,item=engine(7)
    vm.globals().poll();actor=vm.globals().actor
    assert actor.raw[actor[item.symbol]]==5 and actor.archipelago_state.applied_count==7

def test_lua_level_jump_and_victory():
    vm,codec,ap,c,b,item=engine()
    vm.globals().poll()
    vm.execute("actor.level=7; poll()")
    out=json.loads(vm.globals().fs.files["/archipelago/game.json"])
    expected={loc.code for loc in b.locations if loc.event=="level" and loc.level<=7}
    assert set(out["checks"])==expected and not out["goal"]
    assert 790000 not in out["checks"]
    vm.execute('actor.winner="full"; poll()')
    out=json.loads(vm.globals().fs.files["/archipelago/game.json"])
    expected_after_victory={loc.code for loc in b.locations if loc.event in {"level","victory"}}
    assert out["goal"] and set(out["checks"])==expected_after_victory

def test_lua_prefix_change_refused():
    vm,codec,ap,c,b,item=engine()
    vm.globals().poll()
    vm.globals().other_id=c.items["stat:str"].code
    vm.execute('snapshot.receipts[1].item=other_id; fs.files["/archipelago/client.json"]=JSON.encode(snapshot); poll()')
    assert "prefix changed" in ap.last_error
    assert vm.globals().actor.stats[1]==10

def test_lua_unknown_receipt_stops():
    vm,codec,ap,c,b,item=engine()
    vm.execute('snapshot.receipts[1].item=1; fs.files["/archipelago/client.json"]=JSON.encode(snapshot); poll()')
    assert vm.globals().actor.archipelago_state.applied_count==0
    assert "Unknown" in ap.last_error

def test_lua_grant_failure_is_not_retried():
    vm,codec,ap,c,b,item=engine()
    vm.execute('AP.initialize(game,snapshot); actor.learnTalent=function(self,id,force,n) self.raw[id]=1; error("simulated engine failure") end; poll()')
    actor=vm.globals().actor
    assert actor.archipelago_state.applied_count==0
    assert "simulated engine failure" in actor.archipelago_state.error
    before=actor.raw[actor[item.symbol]]
    vm.globals().poll()
    assert actor.raw[actor[item.symbol]]==before

def test_lua_dead_character_not_granted():
    vm,codec,ap,c,b,item=engine()
    vm.execute("actor.dead=true; poll()")
    assert vm.globals().actor.archipelago_state.applied_count==0

def test_lua_different_slot_refused():
    vm,codec,ap,c,b,item=engine()
    vm.globals().poll()
    vm.execute('snapshot.identity.slot=2; fs.files["/archipelago/client.json"]=JSON.encode(snapshot); poll()')
    assert "different AP" in ap.last_error

def test_lua_nonplayer_clone_ignored():
    vm,codec,ap,c,b,item=engine()
    vm.globals().poll()
    assert not vm.eval('AP.isCharacter({archipelago_character=true})')

def test_equipment_requirement_restore_and_slots():
    vm,codec,ap,c,b,item=engine()
    vm.execute(r'''
function actor:canWearObject(object)
  if object.explode then error("validation failed") end
  if object.slot=="unsupported" then return false,"slot" end
  if object.require then return false,"stats" end
  return true,"allowed"
end
loadPrevious=function(...)return actor end
''')
    vm.execute((LUA/"superload/mod/class/Actor.lua").read_text(encoding="utf-8"))
    vm.execute('obj={require={stat=50},level_requirement=40,slot="mainhand"}; allowed=actor:canWearObject(obj)')
    assert vm.globals().allowed is True
    assert vm.globals().obj.require.stat==50 and vm.globals().obj.level_requirement==40
    vm.execute('obj.slot="unsupported"; allowed=actor:canWearObject(obj)')
    assert vm.globals().allowed is False
    vm.execute('obj.explode=true; ok=pcall(function()actor:canWearObject(obj)end)')
    assert vm.globals().ok is False and vm.globals().obj.require.stat==50


def test_finger_of_death_optional_capture_needs_possession_and_body_storage():
    vm,codec,ap,c,b,item=engine()
    vm.execute(r'''
poll()
actor.T_POSSESS="T_POSSESS"
actor.T_BODIES_RESERVE="T_BODIES_RESERVE"
function actor:callTalent(tid,method,...)
  return tid..":"..method
end
loadPrevious=function(...)return actor end
''')
    vm.execute((LUA/"superload/mod/class/Actor.lua").read_text(encoding="utf-8"))
    vm.execute(r'''
assert(actor:callTalent(actor.T_POSSESS,"absorbCheck")==nil)
assert(actor:callTalent(actor.T_POSSESS,"basicAbsorbCheck")=="T_POSSESS:basicAbsorbCheck")
actor.raw.T_POSSESS=1
assert(actor:callTalent(actor.T_POSSESS,"absorbCheck")==nil)
actor.raw.T_BODIES_RESERVE=1
assert(actor:callTalent(actor.T_POSSESS,"absorbCheck")=="T_POSSESS:absorbCheck")
actor.archipelago_character=false
actor.raw.T_BODIES_RESERVE=0
assert(actor:callTalent(actor.T_POSSESS,"absorbCheck")=="T_POSSESS:absorbCheck")
''')
