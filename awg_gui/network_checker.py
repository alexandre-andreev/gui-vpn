"""Background internet connectivity checker with debounce."""

import socket
import threading
from collections.abc import Callable
from typing import Any

import requests

_PROBE_URL = "https://www.google.com/generate_204"
_PROBE_TIMEOUT = 3.0
_FALLBACK_HOST = ("8.8.8.8", 53)
_FALLBACK_TIMEOUT = 3.0


def _check_once() -> bool:
    """Return True if the internet is reachable.

    Tries an HTTP probe first; falls back to a TCP connect to 8.8.8.8:53.
    """
    try:
        resp = requests.get(_PROBE_URL, timeout=_PROBE_TIMEOUT)
        if resp.status_code == 204:
            return True
    except Exception:
        pass
    try:
        with socket.create_connection(_FALLBACK_HOST, timeout=_FALLBACK_TIMEOUT):
            return True
    except OSError:
        return False


class NetworkChecker:
    """Polls internet connectivity in a background daemon thread.

    Calls on_status_change(connected) when connectivity state changes.
    Requires 2 consecutive identical probe results before reporting a change
    (debounce), except for the very first result which is reported immediately.
    """

    def __init__(
        self,
        on_status_change: Callable[[bool], Any],
        interval: float = 7.0,
    ) -> None:
        self._callback = on_status_change
        self._interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._connected: bool | None = None
        self._pending: bool | None = None
        self._consecutive = 0

    def start(self) -> None:
        """Start background connectivity polling (idempotent)."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="network-checker")
        self._thread.start()

    def stop(self) -> None:
        """Stop background polling and block until the thread exits."""
        self._stop.set()
        if self._thread:
            self._thread.join()

    def _loop(self) -> None:
        while True:
            result = _check_once()
            self._update(result)
            if self._stop.wait(self._interval):
                break

    def _update(self, result: bool) -> None:
        """Apply debounce and fire callback on confirmed state transition."""
        if self._connected is None:
            # First ever result: report immediately, no debounce needed.
            self._connected = result
            self._pending = result
            self._consecutive = 1
            self._callback(result)
            return

        if result == self._pending:
            self._consecutive += 1
        else:
            self._pending = result
            self._consecutive = 1

        if self._consecutive >= 2 and result != self._connected:
            self._connected = result
            self._callback(result)
