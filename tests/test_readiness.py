from random import Random
import pytest
from tome_ap.generation import Settings,create_build,readiness_thresholds
from .factories import fixture_catalog

def test_initial_band_has_no_requirements():
    c=fixture_catalog();b=create_build(c,Settings(logic_mode="readiness"),Random(1))
    assert readiness_thresholds(c,b,2)==(0,0)

def test_final_band_is_half_ranks_and_40_percent_stats():
    c=fixture_catalog();b=create_build(c,Settings(logic_mode="readiness"),Random(1))
    assert readiness_thresholds(c,b,0)==(117,24)

@pytest.mark.parametrize("count",[4,6,8,10,12])
def test_thresholds_monotonic_and_scaled(count):
    c=fixture_catalog();b=create_build(c,Settings(class_tree_count=count,logic_mode="readiness"),Random(1))
    thresholds=[readiness_thresholds(c,b,l) for l in range(2,41)]
    assert thresholds==sorted(thresholds)
    assert thresholds[-1][0]==((count+4)*20 + 35)//2
