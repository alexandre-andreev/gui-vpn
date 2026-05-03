"""VPN service controller — wraps systemctl and manages wg0.conf via pkexec."""

import hashlib
import os
import subprocess
from pathlib import Path

SERVICE = "awg-quick@wg0.service"
WG0_CONF = Path("/etc/amnezia/amneziawg/wg0.conf")
WG0_ORIGINAL = Path("/etc/amnezia/amneziawg/wg0.conf.original")


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


def _pkexec(*args: str) -> subprocess.CompletedProcess:
    return _run(["pkexec", *args])


def start() -> None:
    """Start the VPN tunnel."""
    _pkexec("systemctl", "start", SERVICE)


def stop() -> None:
    """Stop the VPN tunnel."""
    _pkexec("systemctl", "stop", SERVICE)


def is_active() -> bool:
    """Return True if the VPN tunnel is currently running."""
    return _run(["systemctl", "is-active", SERVICE], check=False).returncode == 0


def enable_autostart() -> None:
    """Enable VPN autostart on boot."""
    _pkexec("systemctl", "enable", SERVICE)


def disable_autostart() -> None:
    """Disable VPN autostart on boot."""
    _pkexec("systemctl", "disable", SERVICE)


def is_autostart_enabled() -> bool:
    """Return True if the VPN service is enabled for autostart."""
    return _run(["systemctl", "is-enabled", SERVICE], check=False).returncode == 0


def _ensure_backup() -> None:
    """Create wg0.conf.original on the first run if it does not exist yet."""
    if not WG0_ORIGINAL.exists():
        _pkexec("cp", str(WG0_CONF), str(WG0_ORIGINAL))


def apply_config(config_path: Path) -> None:
    """Atomically replace wg0.conf with config_path, creating a backup first.

    Steps:
      1. Ensure wg0.conf.original exists (first-run backup).
      2. pkexec cp <config_path> <wg0.conf.tmp.<pid>>
      3. pkexec mv <tmp> <wg0.conf>   — rename(2) is atomic on the same FS.
    """
    _ensure_backup()
    tmp = WG0_CONF.parent / f"wg0.conf.tmp.{os.getpid()}"
    try:
        _pkexec("cp", str(config_path), str(tmp))
        _pkexec("mv", str(tmp), str(WG0_CONF))
    except VpnError:
        try:
            _pkexec("rm", "-f", str(tmp))
        except VpnError:
            pass
        raise


def restore_original() -> None:
    """Restore wg0.conf from the .original backup."""
    if not WG0_ORIGINAL.exists():
        raise VpnError(f"Backup not found: {WG0_ORIGINAL}")
    _pkexec("cp", str(WG0_ORIGINAL), str(WG0_CONF))


def get_active_config_hash() -> str | None:
    """Return SHA-256 hash of the current wg0.conf, or None if unreadable."""
    try:
        return hashlib.sha256(WG0_CONF.read_bytes()).hexdigest()
    except OSError:
        return None
