from awg_gui.autostart import disable, enable, is_enabled


def test_enable_creates_desktop_file(tmp_path):
    p = tmp_path / "autostart" / "awg-gui.desktop"
    enable(p)
    assert p.exists()


def test_enable_creates_parent_dirs(tmp_path):
    p = tmp_path / "a" / "b" / "c" / "awg-gui.desktop"
    enable(p)
    assert p.exists()


def test_desktop_file_contains_exec_entry(tmp_path):
    p = tmp_path / "awg-gui.desktop"
    enable(p)
    assert "Exec=awg-gui" in p.read_text()


def test_desktop_file_has_correct_type(tmp_path):
    p = tmp_path / "awg-gui.desktop"
    enable(p)
    assert "Type=Application" in p.read_text()


def test_disable_removes_file(tmp_path):
    p = tmp_path / "awg-gui.desktop"
    enable(p)
    disable(p)
    assert not p.exists()


def test_disable_is_idempotent(tmp_path):
    p = tmp_path / "awg-gui.desktop"
    disable(p)  # file doesn't exist — should not raise
    disable(p)


def test_is_enabled_true_when_file_exists(tmp_path):
    p = tmp_path / "awg-gui.desktop"
    enable(p)
    assert is_enabled(p) is True


def test_is_enabled_false_when_file_absent(tmp_path):
    p = tmp_path / "awg-gui.desktop"
    assert is_enabled(p) is False


def test_enable_disable_enable_cycle(tmp_path):
    p = tmp_path / "awg-gui.desktop"
    enable(p)
    disable(p)
    enable(p)
    assert is_enabled(p) is True
