"""Persistent application settings stored in ~/.config/awg-gui/config.json."""

import json
from pathlib import Path

_CONFIG_PATH = Path("~/.config/awg-gui/config.json").expanduser()
_DEFAULT_CONFIG_DIR = str(Path("~/Загрузки/vpn-awg").expanduser())


def _defaults() -> dict:
    return {
        "config_dir": _DEFAULT_CONFIG_DIR,
        "last_selected": None,
    }


def load(path: Path = _CONFIG_PATH) -> dict:
    """Return settings dict, merged with defaults for any missing keys."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _defaults()
        return {**_defaults(), **data}
    except (FileNotFoundError, json.JSONDecodeError):
        return _defaults()


def save(cfg: dict, path: Path = _CONFIG_PATH) -> None:
    """Persist settings to disk, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
