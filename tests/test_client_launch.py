from pathlib import Path

from tome_ap.client import _find_ap


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
    assert "ctx.run_gui()" in text
    assert 'input("Mailbox directory:' not in text
