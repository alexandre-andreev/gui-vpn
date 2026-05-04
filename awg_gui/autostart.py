"""XDG autostart entry management for awg-gui."""

import shutil
import sys
from pathlib import Path

_DESKTOP_FILE = Path("~/.config/autostart/awg-gui.desktop").expanduser()

_TEMPLATE = """\
[Desktop Entry]
Type=Application
Name=awg-gui
Comment=AmneziaWG VPN manager
Exec={exec_cmd}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""


def _find_exec() -> str:
    """Return absolute path to the awg-gui executable.

    Priority: system wrapper (/usr/local/bin) → current process → PATH lookup.
    """
    system = Path("/usr/local/bin/awg-gui")
    if system.exists():
        return str(system)
    current = Path(sys.argv[0]).resolve()
    if current.name == "awg-gui":
        return str(current)
    found = shutil.which("awg-gui")
    return found if found else "awg-gui"


def enable(path: Path = _DESKTOP_FILE) -> None:
    """Create the autostart desktop entry using the absolute executable path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_TEMPLATE.format(exec_cmd=_find_exec()))


def disable(path: Path = _DESKTOP_FILE) -> None:
    """Remove the autostart desktop entry."""
    path.unlink(missing_ok=True)


def is_enabled(path: Path = _DESKTOP_FILE) -> bool:
    """Return True if the autostart desktop entry exists."""
    return path.exists()
