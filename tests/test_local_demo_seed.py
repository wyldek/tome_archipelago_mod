from tools import local_demo


def test_explicit_seed_wins():
    saved = {"demo_seed": 99}
    assert local_demo.choose_demo_seed(42, saved, False) == 42
    assert local_demo.choose_demo_seed(42, saved, True) == 42


def test_resume_saved_seed():
    assert local_demo.choose_demo_seed(None, {"demo_seed": 99}, False) == 99


def test_resume_legacy_seed_name():
    saved = {"identity": {"seed_name": "LOCAL-DEMO-12345"}}
    assert local_demo.choose_demo_seed(None, saved, False) == 12345


def test_reset_generates_fresh_seed(monkeypatch):
    monkeypatch.setattr(local_demo.secrets, "randbelow", lambda upper: 777)
    assert local_demo.choose_demo_seed(None, {"demo_seed": 99}, True) == 778


def test_new_demo_generates_seed(monkeypatch):
    monkeypatch.setattr(local_demo.secrets, "randbelow", lambda upper: 123)
    assert local_demo.choose_demo_seed(None, None, False) == 124
