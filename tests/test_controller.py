import queue
from pathlib import Path
from unittest.mock import patch

from awg_gui.config_manager import ConfigEntry
from awg_gui.controller import CONNECTED, CONNECTING, DISCONNECTED, ERROR, Controller
from awg_gui.vpn_service import VpnError

MOD = "awg_gui.controller"


def _entry(tmp_path: Path) -> ConfigEntry:
    path = tmp_path / "GermanyBerlinS7.conf"
    path.write_text("[Interface]")
    return ConfigEntry(
        country="Germany",
        city="Berlin",
        server_id="S7",
        filename="GermanyBerlinS7.conf",
        path=path,
    )


def _drain(q: queue.Queue) -> list[tuple]:
    events = []
    while not q.empty():
        events.append(q.get_nowait())
    return events


# ── load_configs ──────────────────────────────────────────────────────────────


def test_load_configs_returns_entries(tmp_path):
    (tmp_path / "GermanyBerlinS7.conf").write_text("[Interface]")
    q = queue.Queue()
    ctrl = Controller(tmp_path, q)
    entries = ctrl.load_configs()
    assert len(entries) == 1
    assert entries[0].country == "Germany"


def test_load_configs_missing_dir_puts_error():
    q = queue.Queue()
    ctrl = Controller(Path("/nonexistent/dir/xyz"), q)
    entries = ctrl.load_configs()
    assert entries == []
    events = _drain(q)
    assert any(e[0] == "error" for e in events)


# ── connect ───────────────────────────────────────────────────────────────────


def test_connect_puts_connecting_synchronously(tmp_path):
    q = queue.Queue()
    ctrl = Controller(tmp_path, q)
    entry = _entry(tmp_path)
    with patch(f"{MOD}.apply_config"), patch(f"{MOD}.restart"):
        ctrl.connect(entry)
    assert q.get_nowait() == ("status", CONNECTING)


def test_do_connect_success_puts_connected(tmp_path):
    q = queue.Queue()
    ctrl = Controller(tmp_path, q)
    entry = _entry(tmp_path)
    with patch(f"{MOD}.apply_config"), patch(f"{MOD}.restart"):
        ctrl._do_connect(entry)
    events = _drain(q)
    assert ("active_entry", entry) in events
    assert ("status", CONNECTED) in events
    assert ctrl.active_entry is entry


def test_do_connect_vpnerror_puts_error(tmp_path):
    q = queue.Queue()
    ctrl = Controller(tmp_path, q)
    entry = _entry(tmp_path)
    with patch(f"{MOD}.apply_config", side_effect=VpnError("auth")):
        ctrl._do_connect(entry)
    events = _drain(q)
    assert any(e[0] == "error" for e in events)
    assert ("status", ERROR) in events
    assert ctrl.active_entry is None


def test_do_connect_restart_failure_puts_error(tmp_path):
    q = queue.Queue()
    ctrl = Controller(tmp_path, q)
    entry = _entry(tmp_path)
    with patch(f"{MOD}.apply_config"), patch(f"{MOD}.restart", side_effect=VpnError("restart")):
        ctrl._do_connect(entry)
    events = _drain(q)
    assert ("status", ERROR) in events


# ── disconnect ────────────────────────────────────────────────────────────────


def test_do_disconnect_success_puts_disconnected(tmp_path):
    q = queue.Queue()
    ctrl = Controller(tmp_path, q)
    with patch(f"{MOD}.stop"):
        ctrl._do_disconnect()
    events = _drain(q)
    assert ("status", DISCONNECTED) in events
    assert ctrl.active_entry is None


def test_do_disconnect_clears_active_entry(tmp_path):
    q = queue.Queue()
    ctrl = Controller(tmp_path, q)
    entry = _entry(tmp_path)
    ctrl._active_entry = entry
    with patch(f"{MOD}.stop"):
        ctrl._do_disconnect()
    assert ctrl.active_entry is None


def test_do_disconnect_vpnerror_puts_error(tmp_path):
    q = queue.Queue()
    ctrl = Controller(tmp_path, q)
    with patch(f"{MOD}.stop", side_effect=VpnError("stop failed")):
        ctrl._do_disconnect()
    events = _drain(q)
    assert any(e[0] == "error" for e in events)
    assert ("status", ERROR) in events


# ── network callback ──────────────────────────────────────────────────────────


def test_network_change_puts_internet_event(tmp_path):
    q = queue.Queue()
    ctrl = Controller(tmp_path, q)
    ctrl._on_network_change(True)
    assert q.get_nowait() == ("internet", True)
    ctrl._on_network_change(False)
    assert q.get_nowait() == ("internet", False)


# ── network checker lifecycle ─────────────────────────────────────────────────


def test_start_stop_network_checker(tmp_path):
    q = queue.Queue()
    ctrl = Controller(tmp_path, q)
    with (
        patch("awg_gui.network_checker.NetworkChecker.start") as mock_start,
        patch("awg_gui.network_checker.NetworkChecker.stop") as mock_stop,
    ):
        ctrl.start_network_checker()
        ctrl.stop_network_checker()
    mock_start.assert_called_once()
    mock_stop.assert_called_once()


def test_active_entry_property_initially_none(tmp_path):
    q = queue.Queue()
    ctrl = Controller(tmp_path, q)
    assert ctrl.active_entry is None
