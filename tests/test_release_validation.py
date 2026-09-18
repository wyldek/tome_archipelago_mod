from pathlib import Path
from unittest.mock import patch
import zipfile

import pytest

from tools.validate import PACKAGED_FILES, run_standalone, validate_ap_root, verify_apworld


def test_release_rejects_missing_lua_execution_dependency():
    with patch("tools.validate.importlib.util.find_spec", side_effect=lambda name: None if name == "lupa" else object()):
        with pytest.raises(RuntimeError, match="requires lupa"):
            run_standalone()


def test_release_rejects_wrong_ap_tag(tmp_path):
    (tmp_path / "Launcher.py").write_text("")
    with patch("tools.validate.subprocess.check_output", side_effect=["wrong\n", "pinned\n"]):
        with pytest.raises(RuntimeError, match="requires the Archipelago 0.6.7 tag"):
            validate_ap_root(tmp_path)


def test_release_accepts_matching_clean_ap_tag(tmp_path):
    (tmp_path / "Launcher.py").write_text("")
    with patch("tools.validate.subprocess.check_output", side_effect=["pinned\n", "pinned\n", "", ""]):
        assert validate_ap_root(tmp_path) == "pinned"


@pytest.mark.parametrize("broken", [None, "missing", "stale", "duplicate"])
def test_apworld_must_match_tested_staging(tmp_path, broken):
    stage = tmp_path / "stage"
    artifact = tmp_path / "tome.apworld"
    target = "options.py"
    with zipfile.ZipFile(artifact, "w") as archive:
        for name in PACKAGED_FILES:
            source = stage / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(("source:" + name).encode())
            if broken == "missing" and name == target:
                continue
            data = b"stale" if broken == "stale" and name == target else source.read_bytes()
            archive.writestr("tome/" + name, data)
            if broken == "duplicate" and name == target:
                with pytest.warns(UserWarning, match="Duplicate"):
                    archive.writestr("tome/" + name, data)
    if broken:
        with pytest.raises(RuntimeError):
            verify_apworld(artifact, stage)
    else:
        verify_apworld(artifact, stage)
