from pathlib import Path

import pytest

from awg_gui.config_manager import (
    ConfigEntry,
    _parse_stem,
    list_configs,
    read_config,
)

# All 28 real config files (excluding wg0.conf), using actual filename stems.
PARSE_CASES = [
    # (stem, country, city, server_id)
    ("AustriaGrazS1", "Austria", "Graz", "S1"),
    ("BelgiumBrusselsS1", "Belgium", "Brussels", "S1"),
    ("CanadaMontreal", "Canada", "Montreal", ""),
    ("CzechRepublicPragueS1", "Czech Republic", "Prague", "S1"),
    ("DenmarkCopenhagenS1", "Denmark", "Copenhagen", "S1"),
    ("EstoniaTallinnS2", "Estonia", "Tallinn", "S2"),
    ("FinlandHelsinkiS6", "Finland", "Helsinki", "S6"),
    ("FranceParisS1", "France", "Paris", "S1"),
    ("GermanyBerlinS7", "Germany", "Berlin", "S7"),
    ("HongKongCentralDistrictS1", "Hong Kong", "Central District", "S1"),
    ("HungaryBudapestR2", "Hungary", "Budapest", "R2"),
    ("IsraelTelAvivS1", "Israel", "Tel Aviv", "S1"),
    ("KazakhstanAlmatySLOW2", "Kazakhstan", "Almaty", "SLOW2"),
    ("NetherlandsAmsterdamH1", "Netherlands", "Amsterdam", "H1"),
    ("NetherlandsAmsterdamS6", "Netherlands", "Amsterdam", "S6"),
    ("NorwaySandefjordS14", "Norway", "Sandefjord", "S14"),
    ("PolandWarsawS1", "Poland", "Warsaw", "S1"),
    ("RussiaMoscowS2", "Russia", "Moscow", "S2"),
    ("SerbiaBelgradeS3", "Serbia", "Belgrade", "S3"),
    # Actual filename has a space: 'SloveniaLjublj anaS1.conf'
    ("SloveniaLjublj anaS1", "Slovenia", "Ljubljana", "S1"),
    ("SwedenStockholmS1", "Sweden", "Stockholm", "S1"),
    ("TurkeyIstanbulS3", "Turkey", "Istanbul", "S3"),
    ("UnitedKingdomLondonL1", "United Kingdom", "London", "L1"),
    ("USAAshburn", "USA", "Ashburn", ""),
    ("USAKansas", "USA", "Kansas", ""),
    ("USANewYorkCityS2", "USA", "New York City", "S2"),
    ("USASaltLakeCityS1", "USA", "Salt Lake City", "S1"),
    ("USAUtah", "USA", "Utah", ""),
]


@pytest.mark.parametrize("stem,country,city,server_id", PARSE_CASES)
def test_parse_stem(stem, country, city, server_id):
    c, ci, s = _parse_stem(stem)
    assert c == country
    assert ci == city
    assert s == server_id


def test_display_name_with_server_id():
    entry = ConfigEntry(
        country="Austria",
        city="Graz",
        server_id="S1",
        filename="AustriaGrazS1.conf",
        path=Path("AustriaGrazS1.conf"),
    )
    assert entry.display_name == "Austria · Graz · S1"


def test_display_name_without_server_id():
    entry = ConfigEntry(
        country="Canada",
        city="Montreal",
        server_id="",
        filename="CanadaMontreal.conf",
        path=Path("CanadaMontreal.conf"),
    )
    assert entry.display_name == "Canada · Montreal"


def test_missing_directory():
    with pytest.raises(FileNotFoundError, match="Config directory not found"):
        list_configs(Path("/nonexistent/path/that/does/not/exist"))


def test_empty_directory(tmp_path):
    assert list_configs(tmp_path) == []


def test_excludes_wg0_conf(tmp_path):
    (tmp_path / "wg0.conf").write_text("[Interface]")
    (tmp_path / "GermanyBerlinS7.conf").write_text("[Interface]")
    entries = list_configs(tmp_path)
    assert len(entries) == 1
    assert entries[0].filename == "GermanyBerlinS7.conf"


def test_sorted_by_country_then_city(tmp_path):
    for name in ["GermanyBerlinS7.conf", "AustriaGrazS1.conf", "GermanyFrankfurtS1.conf"]:
        (tmp_path / name).write_text("[Interface]")
    entries = list_configs(tmp_path)
    assert [e.country for e in entries] == ["Austria", "Germany", "Germany"]
    assert entries[1].city == "Berlin"
    assert entries[2].city == "Frankfurt"


def test_read_config(tmp_path):
    content = "[Interface]\nAddress = 10.0.0.1/32\n"
    (tmp_path / "GermanyBerlinS7.conf").write_text(content)
    entries = list_configs(tmp_path)
    assert read_config(entries[0]) == content
