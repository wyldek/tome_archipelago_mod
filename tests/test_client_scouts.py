from types import SimpleNamespace
from tome_ap.client import _shop_location_codes, _scout_snapshot

def test_shop_location_codes_only_shop_events():
    contract={"locations":[{"code":1,"event":"level"},{"code":2,"event":"shop"},{"code":3,"event":"shop"}]}
    assert _shop_location_codes(contract)==[2,3]

def test_scout_snapshot_resolves_item_and_recipient():
    info=SimpleNamespace(item=77,location=2,player=4,flags=2)
    class Lookup:
        def lookup_in_slot(self,item,player):
            assert (item,player)==(77,4)
            return "Morph Ball"
    ctx=SimpleNamespace(
        contract={"locations":[{"code":2,"event":"shop"}]},
        locations_info={2:info},item_names=Lookup(),player_names={4:"Samus"},
    )
    assert _scout_snapshot(ctx)==[{"location":2,"item":77,"item_name":"Morph Ball","player":4,"player_name":"Samus","flags":2}]
