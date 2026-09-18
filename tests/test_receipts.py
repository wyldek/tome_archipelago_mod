from copy import deepcopy
from random import Random
import pytest
from tome_ap.generation import create_build,Settings
from tome_ap.model import Identity,Receipt,ValidationError
from tome_ap.receipts import ReceiptStream,ReferenceSave
from .factories import fixture_catalog

def setup():
    c=fixture_catalog();b=create_build(c,Settings(),Random(1));contract=b.contract(c)
    identity=Identity("Test seed",0,1,contract["contract_hash"])
    defs={i["code"]:i for i in contract["items"]}
    return c,b,identity,defs

def test_repeated_ids_are_ranks_not_deduplicated():
    c,b,i,defs=setup();s=ReferenceSave(i)
    item=c.items[b.starters[0]];history=[Receipt(item.code)]*3
    s.apply(i,history,defs)
    assert s.talent_ranks[item.symbol]==3 and s.applied_count==3
    s.apply(i,history,defs)
    assert s.talent_ranks[item.symbol]==3

def test_above_cap_acknowledged():
    c,b,i,defs=setup();s=ReferenceSave(i);item=c.items[b.starters[0]]
    s.apply(i,[Receipt(item.code)]*9,defs)
    assert s.talent_ranks[item.symbol]==5 and s.applied_count==9

def test_specific_stat_and_cap():
    c,b,i,defs=setup();s=ReferenceSave(i)
    s.apply(i,[Receipt(c.items["stat:mag"].code)]*20,defs)
    assert s.stats["mag"]==60 and s.stats["str"]==10 and s.applied_count==20

def test_prodigy_duplicate_noop():
    c,b,i,defs=setup();s=ReferenceSave(i)
    s.apply(i,[Receipt(c.items[b.prodigies[0]].code)]*2,defs)
    assert len(s.prodigies)==1 and s.applied_count==2

def test_restore_old_save_replays_missing_grants():
    c,b,i,defs=setup();s=ReferenceSave(i);item=c.items[b.starters[0]]
    history=[Receipt(item.code)]*4
    s.apply(i,history[:2],defs);checkpoint=deepcopy(s)
    s.apply(i,history,defs)
    checkpoint.apply(i,history,defs)
    assert checkpoint==s

def test_wrong_seed_refused():
    c,b,i,defs=setup();s=ReferenceSave(i)
    with pytest.raises(ValidationError):s.apply(Identity("Other",0,1,i.contract_hash),[],defs)

def test_short_history_refused():
    c,b,i,defs=setup();s=ReferenceSave(i)
    s.apply(i,[Receipt(c.items[b.starters[0]].code)],defs)
    with pytest.raises(ValidationError):s.apply(i,[],defs)

def test_unknown_item_does_not_advance():
    c,b,i,defs=setup();s=ReferenceSave(i)
    with pytest.raises(ValidationError):s.apply(i,[Receipt(123)],defs)
    assert s.applied_count==0

def test_stream_overlap_and_gap():
    stream=ReceiptStream();a,b,c=Receipt(1),Receipt(2),Receipt(3)
    assert stream.accept(0,[a,b])
    assert stream.accept(1,[b,c])
    assert stream.items==[a,b,c]
    assert not stream.accept(5,[a]) and stream.need_sync
    assert stream.accept(0,[a,b,c]) and not stream.need_sync

def test_conflicting_overlap_requires_resync():
    stream=ReceiptStream();stream.accept(0,[Receipt(1),Receipt(2)])
    assert not stream.accept(1,[Receipt(3)])
    assert stream.items==[Receipt(1),Receipt(2)]

def test_admin_source_metadata_supported():
    assert Receipt(1,-1,0,0).location==-1
