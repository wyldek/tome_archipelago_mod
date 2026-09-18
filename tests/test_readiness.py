"""Readiness is unavailable, not repaired or silently selected."""
import ast
from pathlib import Path
from random import Random

import pytest

from tome_ap.generation import Settings, create_build
from tome_ap.model import ValidationError
from .factories import fixture_catalog


@pytest.mark.parametrize("mode", ["readiness", "unknown", 1, None])
def test_non_unrestricted_generation_is_rejected(mode):
    with pytest.raises(ValidationError, match="disabled.*unrestricted"):
        create_build(fixture_catalog(), Settings(logic_mode=mode), Random(1))


def test_default_contract_remains_unrestricted():
    catalog = fixture_catalog()
    build = create_build(catalog, Settings(), Random(1))
    assert build.contract(catalog)["settings"]["logic_mode"] == "unrestricted"


def test_no_player_facing_logic_mode():
    path = Path(__file__).resolve().parents[1] / "apworld/tome/options.py"
    module = ast.parse(path.read_text(encoding="utf-8"))
    options = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == "ToMEOptions")
    assert "logic_mode" not in {
        n.target.id for n in options.body if isinstance(n, ast.AnnAssign)
    }
    assert not any(isinstance(n, ast.ClassDef) and n.name == "LogicMode" for n in module.body)
