"""VPN service controller — delegates all privileged ops to awg-gui-helper."""

import hashlib
import subprocess
from pathlib import Path

SERVICE = "awg-quick@wg0.service"
WG0_CONF = Path("/etc/amnezia/amneziawg/wg0.conf")
WG0_ORIGINAL = Path("/etc/amnezia/amneziawg/wg0.conf.original")
HELPER = Path("/usr/local/lib/awg-gui/awg-gui-helper")


class VpnError(Exception):
    """Raised when a VPN operation fails."""


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise VpnError(f"Command not found: {cmd[0]}") from exc
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise VpnError(f"{' '.join(cmd)}\n{detail}" if detail else " ".join(cmd))
    return result


def _helper(*args: str) -> subprocess.CompletedProcess:
    """Run awg-gui-helper via pkexec with the given subcommand and arguments."""
    return _run(["pkexec", str(HELPER), *args])


def start() -> None:
    """Start the VPN tunnel."""
    _helper("start")


def stop() -> None:
    """Stop the VPN tunnel."""
    _helper("stop")


def restart() -> None:
    """Restart the tunnel; starts it if not currently running."""
    _helper("restart")


def is_active() -> bool:
    """Return True if the VPN tunnel is currently running."""
    return _run(["systemctl", "is-active", SERVICE], check=False).returncode == 0


def enable_autostart() -> None:
    """Enable VPN autostart on boot."""
    _helper("enable")


def disable_autostart() -> None:
    """Disable VPN autostart on boot."""
    _helper("disable")


def is_autostart_enabled() -> bool:
    """Return True if the VPN service is enabled for autostart."""
    return _run(["systemctl", "is-enabled", SERVICE], check=False).returncode == 0


def apply_config(config_path: Path) -> None:
    """Atomically replace wg0.conf with config_path via the helper.

    The helper:
      1. Creates wg0.conf.original backup on first run.
      2. Copies config_path to a sibling tmp file.
      3. Renames tmp → wg0.conf  (atomic rename(2) on the same FS).
    """
    _helper("apply-config", str(config_path))


def restore_original() -> None:
    """Restore wg0.conf from the .original backup via the helper."""
    _helper("restore-original")


def get_active_config_hash() -> str | None:
    """Return SHA-256 hash of the current wg0.conf, or None if unreadable."""
    try:
        return hashlib.sha256(WG0_CONF.read_bytes()).hexdigest()
    except OSError:
        return None
