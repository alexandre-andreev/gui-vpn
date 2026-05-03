"""Application-wide logging to ~/.local/share/awg-gui/awg-gui.log."""

import logging
from pathlib import Path

_LOG_PATH = Path("~/.local/share/awg-gui/awg-gui.log").expanduser()


def setup(log_path: Path = _LOG_PATH) -> logging.Logger:
    """Configure and return the root 'awg_gui' logger (idempotent)."""
    logger = logging.getLogger("awg_gui")
    if logger.handlers:
        return logger
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
