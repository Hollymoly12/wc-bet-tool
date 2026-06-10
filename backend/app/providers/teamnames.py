"""Team name ↔ 3-letter code helpers.

Provides a reverse lookup from provider team name strings to our internal
3-letter codes, plus the shared fixture_id convention both TheOddsApiAdapter
and ApiFootballAdapter use so that odds and fixtures join by construction.
"""
from __future__ import annotations
import logging

from app.seed import seed_data

logger = logging.getLogger(__name__)

# Extra aliases for names commonly used by real data providers that differ
# from our canonical NAMES values.
ALIASES: dict[str, str] = {
    # USA
    "united states":        "USA",
    "us":                   "USA",
    # South Korea
    "korea republic":       "KOR",
    "republic of korea":    "KOR",
    # Turkey
    "turkey":               "TUR",
    "turkiye":              "TUR",
    # Ivory Coast
    "cote d'ivoire":        "CIV",
    "côte d'ivoire":        "CIV",
    "ivory coast":          "CIV",
    # Iran
    "ir iran":              "IRN",
    # New Zealand
    "new zealand":          "NZL",
    # Saudi Arabia
    "saudi arabia":         "KSA",
    # Costa Rica
    "costa rica":           "CRC",
    # "côte d'ivoire" without accent
    "cote divoire":         "CIV",
}


def _build_reverse_map() -> dict[str, str]:
    """Build a case-insensitive name → code map from NAMES + ALIASES."""
    rev: dict[str, str] = {}
    for code, name in seed_data.NAMES.items():
        rev[name.lower().strip()] = code
    for alias, code in ALIASES.items():
        rev[alias.lower().strip()] = code
    return rev


_REVERSE: dict[str, str] = _build_reverse_map()


def to_code(name: str) -> str | None:
    """Normalize a provider team name to our 3-letter code.

    Returns None (and logs a warning) if the name is unrecognised.
    """
    key = name.lower().strip()
    code = _REVERSE.get(key)
    if code is None:
        logger.warning("teamnames: unrecognised team name %r", name)
    return code


def fixture_id(home_code: str, away_code: str) -> str:
    """Canonical fixture identifier: '{HOME}_{AWAY}'."""
    return f"{home_code}_{away_code}"
