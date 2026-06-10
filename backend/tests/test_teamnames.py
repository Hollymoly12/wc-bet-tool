"""Tests for teamnames.to_code — asserts all 48 real WC2026 teams resolve."""
from __future__ import annotations

import pytest

from app.providers.teamnames import to_code

# ---------------------------------------------------------------------------
# 48-team fixture: (provider_name, expected_code)
# Groups A-L as defined in project spec, covering all 48 WC2026 participants.
# Includes common aliases used by The Odds API / API-Football.
# ---------------------------------------------------------------------------
TEAM_NAME_CASES: list[tuple[str, str]] = [
    # Group A
    ("Mexico",              "MEX"),
    ("South Africa",        "RSA"),
    ("Czech Republic",      "CZE"),
    ("South Korea",         "KOR"),
    # Group B
    ("Canada",              "CAN"),
    ("Qatar",               "QAT"),
    ("Switzerland",         "SUI"),
    ("Bosnia & Herzegovina","BIH"),
    # Group C
    ("USA",                 "USA"),
    ("United States",       "USA"),
    ("Paraguay",            "PAR"),
    ("Turkey",              "TUR"),
    ("Türkiye",             "TUR"),
    ("Australia",           "AUS"),
    # Group D
    ("Brazil",              "BRA"),
    ("Morocco",             "MAR"),
    ("Scotland",            "SCO"),
    ("Haiti",               "HAI"),
    # Group E
    ("Germany",             "GER"),
    ("Ecuador",             "ECU"),
    ("Ivory Coast",         "CIV"),
    ("Côte d'Ivoire",       "CIV"),
    ("Curaçao",             "CUW"),
    ("Curacao",             "CUW"),
    # Group F
    ("Netherlands",         "NED"),
    ("Japan",               "JPN"),
    ("Tunisia",             "TUN"),
    ("Sweden",              "SWE"),
    # Group G
    ("Spain",               "ESP"),
    ("Uruguay",             "URU"),
    ("Saudi Arabia",        "KSA"),
    ("Cape Verde",          "CPV"),
    ("Cabo Verde",          "CPV"),
    # Group H
    ("Belgium",             "BEL"),
    ("Egypt",               "EGY"),
    ("Iran",                "IRN"),
    ("IR Iran",             "IRN"),
    ("New Zealand",         "NZL"),
    # Group I
    ("France",              "FRA"),
    ("Senegal",             "SEN"),
    ("Norway",              "NOR"),
    ("Iraq",                "IRQ"),
    # Group J
    ("Argentina",           "ARG"),
    ("Algeria",             "ALG"),
    ("Austria",             "AUT"),
    ("Jordan",              "JOR"),
    # Group K
    ("Portugal",            "POR"),
    ("Colombia",            "COL"),
    ("Uzbekistan",          "UZB"),
    ("DR Congo",            "COD"),
    ("Congo DR",            "COD"),
    ("Democratic Republic of Congo", "COD"),
    # Group L
    ("England",             "ENG"),
    ("Croatia",             "CRO"),
    ("Ghana",               "GHA"),
    ("Panama",              "PAN"),
    # Extra aliases
    ("Korea Republic",      "KOR"),
    ("Bosnia and Herzegovina", "BIH"),
]


@pytest.mark.parametrize("name,expected", TEAM_NAME_CASES)
def test_to_code_resolves(name, expected):
    """to_code must resolve every real WC2026 provider name to its 3-letter code."""
    assert to_code(name) == expected


def test_unknown_name_returns_none():
    """An unrecognised name must return None (not raise)."""
    assert to_code("Atlantis FC") is None


def test_case_insensitive():
    """Resolution must be case-insensitive."""
    assert to_code("spain") == "ESP"
    assert to_code("FRANCE") == "FRA"
    assert to_code("czech republic") == "CZE"
    assert to_code("SOUTH AFRICA") == "RSA"
