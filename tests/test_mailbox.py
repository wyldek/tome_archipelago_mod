from copy import deepcopy
from random import Random
import json
import pytest
from tome_ap.model import Identity,Receipt,ValidationError
from tome_ap.generation import Settings,create_build
from tome_ap.mailbox import atomic_write_json,read_json,validate_contract,client_snapshot,validate_game_snapshot
from .factories import fixture_catalog

def data():
    c=fixture_catalog();b=create_build(c,Settings(),Random(2));contract=b.contract(c)
    ident=Identity("Seed",0,1,contract["contract_hash"])
    return c,b,contract,ident

def test_atomic_roundtrip(tmp_path):
    p=tmp_path/"client.json";atomic_write_json(p,{"hello":"Maj’Eyal", "n":5})
    assert read_json(p)=={"hello":"Maj’Eyal","n":5}
    assert not list(tmp_path.glob("*.tmp"))

def test_partial_snapshot_ignored(tmp_path):
    p=tmp_path/"game.json";p.write_text('{"hello":',encoding="utf-8")
    assert read_json(p) is None

def test_size_limit(tmp_path):
    p=tmp_path/"game.json";p.write_text("{}"*20)
    with pytest.raises(ValidationError):read_json(p,10)

def test_nan_rejected(tmp_path):
    p=tmp_path/"game.json";p.write_text('{"x":NaN}')
    with pytest.raises(ValidationError):read_json(p)

def test_contract_hash_tampering():
    c,b,contract,i=data();bad=deepcopy(contract);bad["shuffled_count"]+=1
    with pytest.raises(ValidationError):validate_contract(bad)

def test_valid_client_snapshot():
    c,b,contract,i=data();snapshot=client_snapshot(i,contract,[Receipt(c.items[b.starters[0]].code)],set(),1,True)
    assert snapshot["complete"] and snapshot["receipts"][0]["item"]==c.items[b.starters[0]].code
    assert snapshot["scouted_locations"] == []

def test_valid_scouted_shop_item():
    c,b,contract,i=data()
    shop=next(loc for loc in b.locations if loc.event=="shop")
    scout=dict(location=shop.code,item=987654321,item_name="Morph Ball",player=2,player_name="Samus",flags=2)
    snapshot=client_snapshot(i,contract,[],set(),1,True,[scout])
    assert snapshot["scouted_locations"] == [scout]

def test_invalid_scout_location_refused():
    c,b,contract,i=data()
    scout=dict(location=9,item=123,item_name="Nope",player=2,player_name="Samus",flags=0)
    with pytest.raises(ValidationError):
        client_snapshot(i,contract,[],set(),1,True,[scout])

def test_wrong_contract_binding():
    c,b,contract,i=data()
    with pytest.raises(ValidationError):client_snapshot(Identity("Seed",0,1,"0"*64),contract,[],set(),1,True)

def test_unknown_received_item():
    c,b,contract,i=data()
    with pytest.raises(ValidationError):client_snapshot(i,contract,[Receipt(1)],set(),1,True)

def test_valid_game_outbox():
    c,b,contract,i=data();active={loc.code for loc in b.locations}
    game=dict(protocol=1,complete=True,identity=i.to_dict(),applied_count=2,revision=4,checks=[b.locations[0].code],goal=False)
    assert validate_game_snapshot(game,i,active)==game

def test_unknown_location_refused():
    c,b,contract,i=data();active={loc.code for loc in b.locations}
    game=dict(protocol=1,complete=True,identity=i.to_dict(),applied_count=2,revision=4,checks=[9],goal=False)
    with pytest.raises(ValidationError):validate_game_snapshot(game,i,active)

def test_cross_seed_checks_refused():
    c,b,contract,i=data();active={loc.code for loc in b.locations}
    game=dict(protocol=1,complete=True,identity=Identity("Other",0,1,i.contract_hash).to_dict(),applied_count=0,revision=1,checks=[],goal=False)
    with pytest.raises(ValidationError):validate_game_snapshot(game,i,active)
