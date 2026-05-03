"""Tests for vpn_service — mocks subprocess so no root is needed."""

import hashlib
from unittest.mock import MagicMock, patch

import pytest

from awg_gui.vpn_service import (
    HELPER,
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
H = str(HELPER)  # expected helper path in command arrays


def _ok(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    return MagicMock(returncode=returncode, stdout=stdout, stderr=stderr)


# ── helper dispatch ───────────────────────────────────────────────────────────


def test_start_calls_helper():
    with patch(f"{MOD}.subprocess.run", return_value=_ok()) as mock:
        start()
    mock.assert_called_once_with(["pkexec", H, "start"], capture_output=True, text=True)


def test_stop_calls_helper():
    with patch(f"{MOD}.subprocess.run", return_value=_ok()) as mock:
        stop()
    mock.assert_called_once_with(["pkexec", H, "stop"], capture_output=True, text=True)


def test_restart_calls_helper():
    with patch(f"{MOD}.subprocess.run", return_value=_ok()) as mock:
        restart()
    mock.assert_called_once_with(["pkexec", H, "restart"], capture_output=True, text=True)


def test_enable_autostart_calls_helper():
    with patch(f"{MOD}.subprocess.run", return_value=_ok()) as mock:
        enable_autostart()
    mock.assert_called_once_with(["pkexec", H, "enable"], capture_output=True, text=True)


def test_disable_autostart_calls_helper():
    with patch(f"{MOD}.subprocess.run", return_value=_ok()) as mock:
        disable_autostart()
    mock.assert_called_once_with(["pkexec", H, "disable"], capture_output=True, text=True)


def test_apply_config_calls_helper(tmp_path):
    conf = tmp_path / "GermanyBerlinS7.conf"
    conf.write_text("[Interface]")
    with patch(f"{MOD}.subprocess.run", return_value=_ok()) as mock:
        apply_config(conf)
    mock.assert_called_once_with(
        ["pkexec", H, "apply-config", str(conf)], capture_output=True, text=True
    )


def test_restore_original_calls_helper():
    with patch(f"{MOD}.subprocess.run", return_value=_ok()) as mock:
        restore_original()
    mock.assert_called_once_with(["pkexec", H, "restore-original"], capture_output=True, text=True)


# ── is_active / is_autostart_enabled (no helper) ─────────────────────────────


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
    with patch(f"{MOD}.subprocess.run", return_value=_ok(1)):
        with pytest.raises(VpnError):
            start()


def test_raises_vpn_error_on_command_not_found():
    with patch(f"{MOD}.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(VpnError, match="Command not found"):
            start()


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
