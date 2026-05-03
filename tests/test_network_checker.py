from unittest.mock import MagicMock, patch

from awg_gui.network_checker import NetworkChecker, _check_once

MOD = "awg_gui.network_checker"


# ── _check_once ───────────────────────────────────────────────────────────────


def test_check_once_true_on_204():
    with patch(f"{MOD}.requests.get", return_value=MagicMock(status_code=204)):
        assert _check_once() is True


def test_check_once_falls_back_to_socket_on_non_204():
    """Non-204 response is not sufficient; socket fallback decides."""
    with patch(f"{MOD}.requests.get", return_value=MagicMock(status_code=200)):
        with patch(f"{MOD}.socket.create_connection", return_value=MagicMock()):
            assert _check_once() is True


def test_check_once_false_when_non_204_and_socket_fails():
    with patch(f"{MOD}.requests.get", return_value=MagicMock(status_code=200)):
        with patch(f"{MOD}.socket.create_connection", side_effect=OSError):
            assert _check_once() is False


def test_check_once_falls_back_to_socket_on_requests_exception():
    with patch(f"{MOD}.requests.get", side_effect=Exception("timeout")):
        with patch(f"{MOD}.socket.create_connection", return_value=MagicMock()):
            assert _check_once() is True


def test_check_once_false_when_both_fail():
    with patch(f"{MOD}.requests.get", side_effect=Exception("timeout")):
        with patch(f"{MOD}.socket.create_connection", side_effect=OSError):
            assert _check_once() is False


def test_check_once_false_on_connection_error():
    with patch(f"{MOD}.requests.get", side_effect=Exception("ConnectionError")):
        with patch(f"{MOD}.socket.create_connection", side_effect=OSError):
            assert _check_once() is False


# ── debounce logic (_update) ──────────────────────────────────────────────────


def _checker() -> tuple[NetworkChecker, list[bool]]:
    events: list[bool] = []
    return NetworkChecker(on_status_change=events.append), events


def test_first_result_reported_immediately():
    checker, events = _checker()
    checker._update(True)
    assert events == [True]


def test_second_identical_result_does_not_fire():
    checker, events = _checker()
    checker._update(True)
    checker._update(True)
    assert events == [True]


def test_single_failure_does_not_change_connected_state():
    checker, events = _checker()
    checker._update(True)  # initial → connected
    checker._update(False)  # 1st failure → debounce
    assert events == [True]
    assert checker._connected is True


def test_two_consecutive_failures_disconnect():
    checker, events = _checker()
    checker._update(True)
    checker._update(False)
    checker._update(False)
    assert events == [True, False]


def test_single_recovery_does_not_change_disconnected_state():
    checker, events = _checker()
    checker._update(False)
    checker._update(True)
    assert events == [False]
    assert checker._connected is False


def test_two_consecutive_recoveries_reconnect():
    checker, events = _checker()
    checker._update(False)
    checker._update(True)
    checker._update(True)
    assert events == [False, True]


def test_interrupted_sequence_resets_consecutive_count():
    """fail-succeed-fail should NOT trigger a disconnect."""
    checker, events = _checker()
    checker._update(True)  # initial → connected
    checker._update(False)  # 1st failure
    checker._update(True)  # recovery → resets pending
    checker._update(False)  # 1st failure again
    assert events == [True]


def test_state_only_changes_once_for_sustained_disconnect():
    checker, events = _checker()
    checker._update(True)
    for _ in range(5):
        checker._update(False)
    assert events == [True, False]


# ── start / stop ──────────────────────────────────────────────────────────────


def test_stop_terminates_thread():
    with patch(f"{MOD}._check_once", return_value=True):
        checker = NetworkChecker(lambda _: None, interval=0.01)
        checker.start()
        checker.stop()
    assert checker._thread is not None
    assert not checker._thread.is_alive()


def test_start_is_idempotent():
    with patch(f"{MOD}._check_once", return_value=True):
        checker = NetworkChecker(lambda _: None, interval=0.01)
        checker.start()
        first_thread = checker._thread
        checker.start()
        assert checker._thread is first_thread
        checker.stop()
