import json

from awg_gui.settings import load, save


def test_load_returns_defaults_when_no_file(tmp_path):
    cfg = load(tmp_path / "config.json")
    assert "config_dir" in cfg
    assert cfg["last_selected"] is None


def test_load_merges_saved_values(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"config_dir": "/custom/path"}))
    cfg = load(p)
    assert cfg["config_dir"] == "/custom/path"
    assert "last_selected" in cfg  # default filled in


def test_load_handles_malformed_json(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("not json {{{")
    cfg = load(p)
    assert "config_dir" in cfg  # falls back to defaults


def test_load_handles_non_dict_json(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("[1, 2, 3]")
    cfg = load(p)
    assert "config_dir" in cfg


def test_save_creates_file(tmp_path):
    p = tmp_path / "sub" / "config.json"
    save({"config_dir": "/x"}, p)
    assert p.exists()


def test_save_writes_valid_json(tmp_path):
    p = tmp_path / "config.json"
    save({"config_dir": "/x", "last_selected": "foo.conf"}, p)
    data = json.loads(p.read_text())
    assert data["config_dir"] == "/x"
    assert data["last_selected"] == "foo.conf"


def test_save_then_load_roundtrip(tmp_path):
    p = tmp_path / "config.json"
    original = {"config_dir": "/my/vpn", "last_selected": "GermanyBerlinS7.conf"}
    save(original, p)
    loaded = load(p)
    assert loaded["config_dir"] == original["config_dir"]
    assert loaded["last_selected"] == original["last_selected"]


def test_save_creates_parent_dirs(tmp_path):
    p = tmp_path / "a" / "b" / "config.json"
    save({"config_dir": "/x"}, p)
    assert p.exists()
