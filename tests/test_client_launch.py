\
from pathlib import Path
import json
import pytest

from tome_ap.client import (
    MAILBOX_MARKER_NAME,
    _find_ap,
    _mailbox_marker_valid,
    _resolve_mailbox,
)


class FakeUtils:
    def __init__(self, cached: Path | None = None, selections=()):
        self.storage = {}
        if cached is not None:
            self.storage = {"tome_archipelago": {"mailbox": str(cached)}}
        self.selections = iter(selections)
        self.messages = []

    def persistent_load(self):
        return self.storage

    def persistent_store(self, category, key, value):
        self.storage.setdefault(category, {})[key] = value

    def open_directory(self, title, suggest):
        return next(self.selections, None)

    def messagebox(self, title, text, error=False):
        self.messages.append((title, text, error))


def make_mailbox(path: Path):
    path.mkdir()
    (path / MAILBOX_MARKER_NAME).write_text(
        json.dumps({
            "schema": 2,
            "game": "Tales of Maj'Eyal",
            "addon": "tome-archipelago",
            "virtual_root": "/archipelago",
        }),
        encoding="utf-8",
    )
    return path


def test_standalone_detects_source_root(tmp_path: Path):
    (tmp_path / "CommonClient.py").write_text("# stub\n", encoding="utf-8")
    source, launcher = _find_ap(tmp_path)
    assert source == tmp_path.resolve()
    assert launcher is None


def test_standalone_detects_frozen_launcher(tmp_path: Path):
    launcher = tmp_path / "ArchipelagoLauncher.exe"
    launcher.write_bytes(b"")
    source, found_launcher = _find_ap(tmp_path)
    assert source is None
    assert found_launcher == launcher.resolve()


def test_apworld_client_uses_gui_mailbox_flow():
    root = Path(__file__).resolve().parents[1]
    text = (root / "apworld" / "tome" / "client.py").read_text(encoding="utf-8")
    assert "Utils.open_directory(" in text
    assert "mailbox-info.json" in text
    assert 'MAILBOX_MARKER_ROOT = "/archipelago"' in text
    assert "ctx.run_gui()" in text
    assert 'input("Mailbox directory:' not in text


def test_mailbox_marker_validation(tmp_path: Path):
    good = make_mailbox(tmp_path / "good")
    bad = tmp_path / "bad"
    bad.mkdir()
    assert _mailbox_marker_valid(good)
    assert not _mailbox_marker_valid(bad)


def test_schema1_marker_is_rejected(tmp_path: Path):
    path = tmp_path / "old"
    path.mkdir()
    (path / MAILBOX_MARKER_NAME).write_text(
        json.dumps({"schema": 1, "game": "Tales of Maj'Eyal", "addon": "tome-archipelago"}),
        encoding="utf-8",
    )
    assert not _mailbox_marker_valid(path)


def test_wrong_virtual_root_is_rejected(tmp_path: Path):
    path = tmp_path / "oldroot"
    path.mkdir()
    (path / MAILBOX_MARKER_NAME).write_text(
        json.dumps({
            "schema": 2,
            "game": "Tales of Maj'Eyal",
            "addon": "tome-archipelago",
            "virtual_root": "/tome/archipelago",
        }),
        encoding="utf-8",
    )
    assert not _mailbox_marker_valid(path)


def test_explicit_invalid_mailbox_is_rejected(tmp_path: Path):
    bad = tmp_path / "bad"
    bad.mkdir()
    with pytest.raises(SystemExit, match="not a Tales of Maj'Eyal Archipelago mailbox"):
        _resolve_mailbox(FakeUtils(), str(bad))


def test_stale_cached_mailbox_reprompts_and_replaces_cache(tmp_path: Path):
    bad = tmp_path / "bad"
    bad.mkdir()
    good = make_mailbox(tmp_path / "good")
    utils = FakeUtils(cached=bad, selections=[str(good)])
    assert _resolve_mailbox(utils, None) == good.resolve()
    assert utils.storage["tome_archipelago"]["mailbox"] == str(good.resolve())


def test_invalid_picker_selection_is_not_cached(tmp_path: Path):
    bad = tmp_path / "bad"
    bad.mkdir()
    good = make_mailbox(tmp_path / "good")
    utils = FakeUtils(selections=[str(bad), str(good)])
    assert _resolve_mailbox(utils, None) == good.resolve()
    assert len(utils.messages) == 1
    assert utils.messages[0][2] is True
