"""Tests for app.services.team_universe.derive_universe."""
from __future__ import annotations

from datetime import datetime, timezone

from app.providers.base import OddsLine
from app.services.team_universe import derive_universe

_NOW = datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# Helpers to build synthetic OddsLine fixtures
# ---------------------------------------------------------------------------

def _h2h(home: str, away: str) -> OddsLine:
    """Minimal h2h OddsLine for a given pair of team codes."""
    return OddsLine(
        market_key=f"h2h:{home}_{away}",
        book="test",
        selection="home",
        dec=2.0,
        captured_at=_NOW,
    )


def _build_12_group_lines() -> list[OddsLine]:
    """Build 12 groups × 6 match combinations = 72 h2h OddsLines."""
    # Real WC2026 groups (codes) as specified in the project
    groups = [
        ["MEX", "RSA", "CZE", "KOR"],   # A
        ["CAN", "QAT", "SUI", "BIH"],   # B
        ["USA", "PAR", "TUR", "AUS"],   # C
        ["BRA", "MAR", "SCO", "HAI"],   # D
        ["GER", "ECU", "CIV", "CUW"],   # E
        ["NED", "JPN", "TUN", "SWE"],   # F
        ["ESP", "URU", "KSA", "CPV"],   # G
        ["BEL", "EGY", "IRN", "NZL"],   # H
        ["FRA", "SEN", "NOR", "IRQ"],   # I
        ["ARG", "ALG", "AUT", "JOR"],   # J
        ["POR", "COL", "UZB", "COD"],   # K
        ["ENG", "CRO", "GHA", "PAN"],   # L
    ]
    lines: list[OddsLine] = []
    for grp in groups:
        # All 6 combinations within the group
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                lines.append(_h2h(grp[i], grp[j]))
    return lines


# ---------------------------------------------------------------------------
# Test: 12 clean groups → real universe returned
# ---------------------------------------------------------------------------

def test_derive_universe_returns_48_teams():
    lines = _build_12_group_lines()
    result = derive_universe(lines)
    assert result is not None
    assert len(result["teams"]) == 48


def test_derive_universe_returns_12_groups():
    lines = _build_12_group_lines()
    result = derive_universe(lines)
    assert result is not None
    letters = {t["group"] for t in result["teams"]}
    assert letters == set("ABCDEFGHIJKL")


def test_derive_universe_group_of_mapping():
    lines = _build_12_group_lines()
    result = derive_universe(lines)
    assert result is not None
    group_of = result["group_of"]
    assert len(group_of) == 48
    # Every team code appears in group_of
    for t in result["teams"]:
        assert t["code"] in group_of
        assert group_of[t["code"]] == t["group"]


def test_derive_universe_team_structure():
    """Each team dict must have code, name, group, colors, str0."""
    lines = _build_12_group_lines()
    result = derive_universe(lines)
    assert result is not None
    for t in result["teams"]:
        assert "code" in t
        assert "name" in t
        assert "group" in t
        assert "colors" in t
        assert "str0" in t
        assert t["str0"] == 60.0
        assert isinstance(t["colors"], list) and len(t["colors"]) == 2


def test_derive_universe_groups_size_4():
    """Every group must have exactly 4 teams."""
    lines = _build_12_group_lines()
    result = derive_universe(lines)
    assert result is not None
    from collections import Counter
    counts = Counter(t["group"] for t in result["teams"])
    for letter, count in counts.items():
        assert count == 4, f"Group {letter} has {count} teams"


def test_derive_universe_deterministic_letter_assignment():
    """Letters are assigned by sorted min code — running twice gives same result."""
    lines = _build_12_group_lines()
    r1 = derive_universe(lines)
    r2 = derive_universe(lines)
    assert r1 is not None and r2 is not None
    g1 = r1["group_of"]
    g2 = r2["group_of"]
    assert g1 == g2


def test_derive_universe_new_teams_have_names():
    """The 9 new teams should have real names, not just their codes."""
    from app.seed import seed_data
    lines = _build_12_group_lines()
    result = derive_universe(lines)
    assert result is not None
    by_code = {t["code"]: t for t in result["teams"]}
    new_codes = ["CZE", "RSA", "BIH", "HAI", "SCO", "CUW", "SWE", "CPV", "COD"]
    for code in new_codes:
        assert code in by_code, f"{code} not in universe"
        assert by_code[code]["name"] == seed_data.NAMES[code]
        assert by_code[code]["colors"] == seed_data.COLORS[code]


# ---------------------------------------------------------------------------
# Test: seed-like list (8 matches, < 12 groups of 4) → returns None
# ---------------------------------------------------------------------------

def test_derive_universe_returns_none_for_seed_data():
    """Seed has 8 matches with ids like 'm1' — no h2h: format → None."""
    from app.seed import seed_data
    now = datetime.now(timezone.utc)
    # Seed OddsLines use market_key "h2h:m1" (not h2h:HOME_AWAY pairs)
    seed_lines = []
    for m in seed_data.MATCHES:
        for sel, dec in zip(("home", "draw", "away"), m["odds"]):
            seed_lines.append(OddsLine(
                market_key=f"h2h:{m['id']}",
                book="seed",
                selection=sel,
                dec=dec,
                captured_at=now,
            ))
    result = derive_universe(seed_lines)
    assert result is None


def test_derive_universe_returns_none_for_incomplete_groups():
    """If only 4 groups of 4 exist, returns None."""
    lines = []
    groups = [
        ["ESP", "FRA", "GER", "ENG"],
        ["BRA", "ARG", "POR", "NED"],
        ["ITA", "BEL", "URU", "COL"],
        ["JPN", "KOR", "AUS", "USA"],
    ]
    for grp in groups:
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                lines.append(_h2h(grp[i], grp[j]))
    result = derive_universe(lines)
    assert result is None


def test_derive_universe_returns_none_for_empty_input():
    """Empty input returns None."""
    assert derive_universe([]) is None
