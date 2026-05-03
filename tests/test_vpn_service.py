import hashlib
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from awg_gui.vpn_service import (
    SERVICE,
    VpnError,
    apply_config,
    disable_autostart,
    enable_autostart,
    get_active_config_hash,
    is_active,
    is_autostart_enabled,
    restart,
    restore_original,
    start,
    stop,
)

MOD = "awg_gui.vpn_service"


def _ok(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    return MagicMock(returncode=returncode, stdout=stdout, stderr=stderr)


# ── systemctl command wiring ──────────────────────────────────────────────────


def test_start_calls_pkexec_systemctl():
    with patch(f"{MOD}.subprocess.run", return_value=_ok()) as mock:
        start()
    mock.assert_called_once_with(
        ["pkexec", "systemctl", "start", SERVICE],
        capture_output=True,
        text=True,
    )


def test_stop_calls_pkexec_systemctl():
    with patch(f"{MOD}.subprocess.run", return_value=_ok()) as mock:
        stop()
    mock.assert_called_once_with(
        ["pkexec", "systemctl", "stop", SERVICE],
        capture_output=True,
        text=True,
    )


def test_enable_autostart_calls_pkexec_systemctl():
    with patch(f"{MOD}.subprocess.run", return_value=_ok()) as mock:
        enable_autostart()
    mock.assert_called_once_with(
        ["pkexec", "systemctl", "enable", SERVICE],
        capture_output=True,
        text=True,
    )


def test_disable_autostart_calls_pkexec_systemctl():
    with patch(f"{MOD}.subprocess.run", return_value=_ok()) as mock:
        disable_autostart()
    mock.assert_called_once_with(
        ["pkexec", "systemctl", "disable", SERVICE],
        capture_output=True,
        text=True,
    )


def test_restart_calls_pkexec_systemctl():
    with patch(f"{MOD}.subprocess.run", return_value=_ok()) as mock:
        restart()
    mock.assert_called_once_with(
        ["pkexec", "systemctl", "restart", SERVICE],
        capture_output=True,
        text=True,
    )


def test_is_active_true():
    with patch(f"{MOD}.subprocess.run", return_value=_ok(0)):
        assert is_active() is True


def test_is_active_false():
    with patch(f"{MOD}.subprocess.run", return_value=_ok(3)):
        assert is_active() is False


def test_is_autostart_enabled_true():
    with patch(f"{MOD}.subprocess.run", return_value=_ok(0)):
        assert is_autostart_enabled() is True


def test_is_autostart_enabled_false():
    with patch(f"{MOD}.subprocess.run", return_value=_ok(1)):
        assert is_autostart_enabled() is False


# ── VpnError propagation ──────────────────────────────────────────────────────


def test_raises_vpn_error_with_stderr():
    with patch(f"{MOD}.subprocess.run", return_value=_ok(1, stderr="auth failed")):
        with pytest.raises(VpnError, match="auth failed"):
            start()


def test_raises_vpn_error_with_stdout_when_no_stderr():
    with patch(f"{MOD}.subprocess.run", return_value=_ok(1, stdout="hint", stderr="")):
        with pytest.raises(VpnError, match="hint"):
            start()


def test_raises_vpn_error_without_detail():
    with patch(f"{MOD}.subprocess.run", return_value=_ok(1, stdout="", stderr="")):
        with pytest.raises(VpnError):
            start()


def test_raises_vpn_error_on_command_not_found():
    with patch(f"{MOD}.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(VpnError, match="Command not found"):
            start()


# ── apply_config: file operations via fake pkexec ─────────────────────────────


def _fake_pkexec(tmp_path: Path):
    """Return a fake _pkexec that performs real file ops inside tmp_path."""

    def fake(*args: str) -> MagicMock:
        match list(args):
            case ["cp", src, dst]:
                shutil.copy2(src, dst)
            case ["mv", src, dst]:
                Path(src).rename(dst)
            case ["rm", "-f", path]:
                Path(path).unlink(missing_ok=True)
        return _ok()

    return fake


def test_apply_config_replaces_wg0(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    original = tmp_path / "wg0.conf.original"
    wg0.write_text("old\n")
    new = tmp_path / "New.conf"
    new.write_text("new\n")

    with (
        patch(f"{MOD}.WG0_CONF", wg0),
        patch(f"{MOD}.WG0_ORIGINAL", original),
        patch(f"{MOD}._pkexec", side_effect=_fake_pkexec(tmp_path)),
    ):
        apply_config(new)

    assert wg0.read_text() == "new\n"


def test_apply_config_creates_backup_on_first_run(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    original = tmp_path / "wg0.conf.original"
    wg0.write_text("original content\n")
    new = tmp_path / "New.conf"
    new.write_text("new\n")

    with (
        patch(f"{MOD}.WG0_CONF", wg0),
        patch(f"{MOD}.WG0_ORIGINAL", original),
        patch(f"{MOD}._pkexec", side_effect=_fake_pkexec(tmp_path)),
    ):
        apply_config(new)

    assert original.read_text() == "original content\n"


def test_apply_config_does_not_overwrite_existing_backup(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    original = tmp_path / "wg0.conf.original"
    wg0.write_text("current\n")
    original.write_text("backup\n")
    new = tmp_path / "New.conf"
    new.write_text("new\n")

    with (
        patch(f"{MOD}.WG0_CONF", wg0),
        patch(f"{MOD}.WG0_ORIGINAL", original),
        patch(f"{MOD}._pkexec", side_effect=_fake_pkexec(tmp_path)),
    ):
        apply_config(new)

    assert original.read_text() == "backup\n"


def test_apply_config_leaves_no_temp_file(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    original = tmp_path / "wg0.conf.original"
    wg0.write_text("old\n")
    new = tmp_path / "New.conf"
    new.write_text("new\n")

    with (
        patch(f"{MOD}.WG0_CONF", wg0),
        patch(f"{MOD}.WG0_ORIGINAL", original),
        patch(f"{MOD}._pkexec", side_effect=_fake_pkexec(tmp_path)),
    ):
        apply_config(new)

    assert not any(f.name.startswith("wg0.conf.tmp.") for f in tmp_path.iterdir())


def test_apply_config_cleans_temp_on_mv_failure(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    original = tmp_path / "wg0.conf.original"
    wg0.write_text("old\n")
    new = tmp_path / "New.conf"
    new.write_text("new\n")

    def failing_pkexec(*args: str) -> MagicMock:
        match list(args):
            case ["cp", src, dst]:
                shutil.copy2(src, dst)
            case ["mv", *_]:
                raise VpnError("mv failed")
            case ["rm", "-f", path]:
                Path(path).unlink(missing_ok=True)
        return _ok()

    with (
        patch(f"{MOD}.WG0_CONF", wg0),
        patch(f"{MOD}.WG0_ORIGINAL", original),
        patch(f"{MOD}._pkexec", side_effect=failing_pkexec),
    ):
        with pytest.raises(VpnError, match="mv failed"):
            apply_config(new)

    assert not any(f.name.startswith("wg0.conf.tmp.") for f in tmp_path.iterdir())
    assert wg0.read_text() == "old\n"


# ── restore_original ──────────────────────────────────────────────────────────


def test_restore_original_copies_backup_to_wg0(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    original = tmp_path / "wg0.conf.original"
    wg0.write_text("current\n")
    original.write_text("backup\n")

    with (
        patch(f"{MOD}.WG0_CONF", wg0),
        patch(f"{MOD}.WG0_ORIGINAL", original),
        patch(f"{MOD}._pkexec", side_effect=_fake_pkexec(tmp_path)),
    ):
        restore_original()

    assert wg0.read_text() == "backup\n"


def test_restore_original_raises_when_no_backup(tmp_path):
    with (
        patch(f"{MOD}.WG0_CONF", tmp_path / "wg0.conf"),
        patch(f"{MOD}.WG0_ORIGINAL", tmp_path / "wg0.conf.original"),
    ):
        with pytest.raises(VpnError, match="Backup not found"):
            restore_original()


# ── get_active_config_hash ────────────────────────────────────────────────────


def test_get_active_config_hash_returns_sha256(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    content = b"[Interface]\nPrivateKey = abc\n"
    wg0.write_bytes(content)

    with patch(f"{MOD}.WG0_CONF", wg0):
        result = get_active_config_hash()

    assert result == hashlib.sha256(content).hexdigest()


def test_get_active_config_hash_returns_none_when_unreadable(tmp_path):
    with patch(f"{MOD}.WG0_CONF", tmp_path / "nonexistent.conf"):
        assert get_active_config_hash() is None
