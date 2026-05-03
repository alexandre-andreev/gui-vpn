"""XDG autostart entry management for awg-gui."""

from pathlib import Path

_DESKTOP_FILE = Path("~/.config/autostart/awg-gui.desktop").expanduser()

_CONTENT = """\
[Desktop Entry]
Type=Application
Name=awg-gui
Comment=AmneziaWG VPN manager
Exec=awg-gui
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""


def enable(path: Path = _DESKTOP_FILE) -> None:
    """Create the autostart desktop entry."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_CONTENT)


def disable(path: Path = _DESKTOP_FILE) -> None:
    """Remove the autostart desktop entry."""
    path.unlink(missing_ok=True)


def is_enabled(path: Path = _DESKTOP_FILE) -> bool:
    """Return True if the autostart desktop entry exists."""
    return path.exists()
