"""Scan VPN config directory and parse filenames into structured entries."""

import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_DIR = Path("/home/alexandre/Загрузки/vpn-awg")

_SERVER_ID_RE = re.compile(r"([A-Z]+\d+)$")

_COUNTRY_DISPLAY: dict[str, str] = {
    "CzechRepublic": "Czech Republic",
    "HongKong": "Hong Kong",
    "UnitedKingdom": "United Kingdom",
}

# Sorted longest-first for greedy prefix matching.
_KNOWN_COUNTRIES: list[str] = sorted(
    [
        "Austria",
        "Belgium",
        "Canada",
        "CzechRepublic",
        "Denmark",
        "Estonia",
        "Finland",
        "France",
        "Germany",
        "HongKong",
        "Hungary",
        "Israel",
        "Kazakhstan",
        "Netherlands",
        "Norway",
        "Poland",
        "Russia",
        "Serbia",
        "Slovenia",
        "Sweden",
        "Turkey",
        "UnitedKingdom",
        "USA",
    ],
    key=len,
    reverse=True,
)


def _split_camel(s: str) -> str:
    """Insert spaces at CamelCase boundaries: 'NewYorkCity' → 'New York City'."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", s)


@dataclass(frozen=True)
class ConfigEntry:
    country: str
    city: str
    server_id: str
    filename: str
    path: Path

    @property
    def display_name(self) -> str:
        parts = [self.country]
        if self.city:
            parts.append(self.city)
        if self.server_id:
            parts.append(self.server_id)
        return " · ".join(parts)


def _parse_stem(stem: str) -> tuple[str, str, str]:
    """Return (country, city, server_id) display strings from a filename stem.

    Handles accidental spaces in stem (e.g. 'SloveniaLjublj anaS1').
    """
    stem = stem.replace(" ", "")

    m = _SERVER_ID_RE.search(stem)
    if m:
        server_id = m.group(1)
        stem = stem[: m.start()]
    else:
        server_id = ""

    country_raw = next((c for c in _KNOWN_COUNTRIES if stem.startswith(c)), None)
    if country_raw is None:
        words = _split_camel(stem).split()
        country_raw = words[0]
        city_raw = "".join(words[1:]) if len(words) > 1 else ""
    else:
        city_raw = stem[len(country_raw) :]

    country = _COUNTRY_DISPLAY.get(country_raw, country_raw)
    city = _split_camel(city_raw) if city_raw else ""

    return country, city, server_id


def list_configs(config_dir: Path = DEFAULT_CONFIG_DIR) -> list[ConfigEntry]:
    """Return sorted list of VPN configs from config_dir, excluding wg0.conf."""
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")

    entries = []
    for path in sorted(config_dir.glob("*.conf")):
        if path.name == "wg0.conf":
            continue
        country, city, server_id = _parse_stem(path.stem)
        entries.append(
            ConfigEntry(
                country=country,
                city=city,
                server_id=server_id,
                filename=path.name,
                path=path,
            )
        )

    return sorted(entries, key=lambda e: (e.country, e.city, e.server_id))


def read_config(entry: ConfigEntry) -> str:
    """Return raw content of a config file."""
    return entry.path.read_text()
