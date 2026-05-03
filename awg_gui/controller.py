"""Orchestrates VPN operations; communicates with UI via a queue."""

import logging
import queue
import threading
from pathlib import Path

from .config_manager import ConfigEntry, list_configs
from .network_checker import NetworkChecker
from .vpn_service import VpnError, apply_config, restart, stop

logger = logging.getLogger("awg_gui")

# Status tokens sent on the queue
DISCONNECTED = "disconnected"
CONNECTING = "connecting"
CONNECTED = "connected"
ERROR = "error"


class Controller:
    """Runs privileged VPN operations in daemon threads and puts results on
    a queue that the UI drains with root.after().

    Queue message format: (event_name: str, data: Any)
    Events:
      ("status",       DISCONNECTED | CONNECTING | CONNECTED | ERROR)
      ("active_entry", ConfigEntry | None)
      ("error",        str)
      ("internet",     bool)
    """

    def __init__(self, config_dir: Path, update_queue: queue.Queue) -> None:
        self._config_dir = config_dir
        self._q = update_queue
        self._active_entry: ConfigEntry | None = None
        self._net = NetworkChecker(self._on_network_change)

    # ── public API ────────────────────────────────────────────────────────────

    def load_configs(self) -> list[ConfigEntry]:
        """Return config list; puts an error event if directory is missing."""
        try:
            return list_configs(self._config_dir)
        except FileNotFoundError as exc:
            self._q.put(("error", str(exc)))
            return []

    def connect(self, entry: ConfigEntry) -> None:
        """Apply config and (re)start the tunnel in a background thread."""
        self._q.put(("status", CONNECTING))
        threading.Thread(target=self._do_connect, args=(entry,), daemon=True).start()

    def disconnect(self) -> None:
        """Stop the tunnel in a background thread."""
        threading.Thread(target=self._do_disconnect, daemon=True).start()

    def start_network_checker(self) -> None:
        self._net.start()

    def stop_network_checker(self) -> None:
        self._net.stop()

    @property
    def active_entry(self) -> ConfigEntry | None:
        return self._active_entry

    # ── background workers ────────────────────────────────────────────────────

    def _do_connect(self, entry: ConfigEntry) -> None:
        try:
            apply_config(entry.path)
            restart()
            self._active_entry = entry
            self._q.put(("active_entry", entry))
            self._q.put(("status", CONNECTED))
            logger.info("Connected: %s", entry.display_name)
        except VpnError as exc:
            logger.error("Connect failed: %s", exc)
            self._q.put(("error", str(exc)))
            self._q.put(("status", ERROR))

    def _do_disconnect(self) -> None:
        try:
            stop()
            self._active_entry = None
            self._q.put(("active_entry", None))
            self._q.put(("status", DISCONNECTED))
            logger.info("Disconnected")
        except VpnError as exc:
            logger.error("Disconnect failed: %s", exc)
            self._q.put(("error", str(exc)))
            self._q.put(("status", ERROR))

    def _on_network_change(self, connected: bool) -> None:
        self._q.put(("internet", connected))
