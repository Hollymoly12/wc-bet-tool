"""Tests for TheOddsApiAdapter — monkeypatches the internal _get helper
so no real HTTP calls are made.
"""
from __future__ import annotations

import pytest

from app.providers.the_odds_api import TheOddsApiAdapter

# ---------------------------------------------------------------------------
# Representative sample payload: 1 event (Spain vs Croatia), 2 bookmakers,
# each with h2h outcomes.
# ---------------------------------------------------------------------------
SAMPLE_EVENTS = [
    {
        "id": "abc123",
        "sport_key": "soccer_fifa_world_cup",
        "home_team": "Spain",
        "away_team": "Croatia",
        "bookmakers": [
            {
                "key": "bet365",
                "title": "Bet365",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Spain",   "price": 1.62},
                            {"name": "Croatia", "price": 5.80},
                            {"name": "Draw",    "price": 4.00},
                        ],
                    }
                ],
            },
            {
                "key": "pinnacle",
                "title": "Pinnacle",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Spain",   "price": 1.65},
                            {"name": "Croatia", "price": 5.50},
                            {"name": "Draw",    "price": 3.90},
                        ],
                    }
                ],
            },
        ],
    }
]


@pytest.fixture()
def adapter(monkeypatch):
    """Return adapter with _get monkeypatched to return SAMPLE_EVENTS."""
    a = TheOddsApiAdapter.__new__(TheOddsApiAdapter)
    a._base = "https://api.the-odds-api.com/v4"
    a._key = "test-key"

    def fake_get(url, params):
        return SAMPLE_EVENTS

    monkeypatch.setattr(a, "_get", fake_get)
    return a


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------

def test_returns_six_lines(adapter):
    """1 event × 2 bookmakers × 3 outcomes = 6 OddsLine objects."""
    lines = adapter.fetch_odds()
    assert len(lines) == 6


def test_market_key(adapter):
    """All lines carry market_key == 'h2h:ESP_CRO'."""
    lines = adapter.fetch_odds()
    for line in lines:
        assert line.market_key == "h2h:ESP_CRO"


def test_selections_present(adapter):
    """Each of home / draw / away appears at least once."""
    lines = adapter.fetch_odds()
    selections = {ln.selection for ln in lines}
    assert selections == {"home", "draw", "away"}


def test_dec_values_match_sample(adapter):
    """Spot-check prices from Bet365 row."""
    lines = adapter.fetch_odds()
    bet365 = [ln for ln in lines if ln.book == "Bet365"]
    assert len(bet365) == 3
    by_sel = {ln.selection: ln.dec for ln in bet365}
    assert by_sel["home"] == pytest.approx(1.62)
    assert by_sel["away"] == pytest.approx(5.80)
    assert by_sel["draw"] == pytest.approx(4.00)


def test_captured_at_set(adapter):
    """captured_at must be a timezone-aware datetime."""
    from datetime import timezone
    lines = adapter.fetch_odds()
    for ln in lines:
        assert ln.captured_at.tzinfo is not None
        assert ln.captured_at.tzinfo == timezone.utc


def test_unknown_team_skipped(monkeypatch):
    """Events with unresolvable team names are silently skipped."""
    bad_events = [
        {
            "id": "bad1",
            "home_team": "Atlantis FC",
            "away_team": "Spain",
            "bookmakers": [],
        }
    ]
    a = TheOddsApiAdapter.__new__(TheOddsApiAdapter)
    a._base = "https://api.the-odds-api.com/v4"
    a._key = "test-key"
    monkeypatch.setattr(a, "_get", lambda url, params: bad_events)
    assert a.fetch_odds() == []


def test_empty_response(monkeypatch):
    """Empty list from API returns empty list of lines."""
    a = TheOddsApiAdapter.__new__(TheOddsApiAdapter)
    a._base = "https://api.the-odds-api.com/v4"
    a._key = "test-key"
    monkeypatch.setattr(a, "_get", lambda url, params: [])
    assert a.fetch_odds() == []


# ---------------------------------------------------------------------------
# fetch_outrights tests
# ---------------------------------------------------------------------------

SAMPLE_OUTRIGHTS_EVENTS = [
    {
        "id": "outright1",
        "sport_key": "soccer_fifa_world_cup_winner",
        "bookmakers": [
            {
                "key": "bet365",
                "title": "Bet365",
                "markets": [
                    {
                        "key": "outrights",
                        "outcomes": [
                            {"name": "Spain",     "price": 5.8},
                            {"name": "France",    "price": 6.5},
                            {"name": "No Winner", "price": 1001.0},
                        ],
                    }
                ],
            },
            {
                "key": "pinnacle",
                "title": "Pinnacle",
                "markets": [
                    {
                        "key": "outrights",
                        "outcomes": [
                            {"name": "Spain",     "price": 5.5},
                            {"name": "France",    "price": 6.0},
                            # "Field" should be skipped
                            {"name": "Field",     "price": 2.0},
                        ],
                    }
                ],
            },
        ],
    }
]


@pytest.fixture()
def outright_adapter(monkeypatch):
    """Adapter with _get monkeypatched to return SAMPLE_OUTRIGHTS_EVENTS."""
    a = TheOddsApiAdapter.__new__(TheOddsApiAdapter)
    a._base = "https://api.the-odds-api.com/v4"
    a._key = "test-key"
    monkeypatch.setattr(a, "_get", lambda url, params: SAMPLE_OUTRIGHTS_EVENTS)
    return a


def test_fetch_outrights_returns_lines(outright_adapter):
    """Should return OddsLine for each resolvable outcome (Spain, France × 2 books = 4 lines)."""
    lines = outright_adapter.fetch_outrights()
    # Spain × 2 books + France × 2 books = 4; "No Winner" and "Field" skipped
    assert len(lines) == 4


def test_fetch_outrights_market_key(outright_adapter):
    """All outright lines must carry market_key == 'outright'."""
    lines = outright_adapter.fetch_outrights()
    for line in lines:
        assert line.market_key == "outright"


def test_fetch_outrights_code_mapping(outright_adapter):
    """Spain must map to ESP, France to FRA."""
    lines = outright_adapter.fetch_outrights()
    selections = {ln.selection for ln in lines}
    assert "ESP" in selections
    assert "FRA" in selections


def test_fetch_outrights_dec_value(outright_adapter):
    """Bet365 Spain dec must be 5.8."""
    lines = outright_adapter.fetch_outrights()
    bet365_esp = [ln for ln in lines if ln.book == "Bet365" and ln.selection == "ESP"]
    assert len(bet365_esp) == 1
    assert bet365_esp[0].dec == pytest.approx(5.8)


def test_fetch_outrights_skips_unresolvable(outright_adapter):
    """'No Winner' and 'Field' must be skipped (not appear in selection codes)."""
    lines = outright_adapter.fetch_outrights()
    selections = {ln.selection for ln in lines}
    assert "No Winner" not in selections
    assert "Field" not in selections


def test_fetch_outrights_captured_at_utc(outright_adapter):
    """captured_at must be UTC-aware."""
    from datetime import timezone
    lines = outright_adapter.fetch_outrights()
    for ln in lines:
        assert ln.captured_at.tzinfo == timezone.utc


def test_fetch_outrights_empty_response(monkeypatch):
    """Empty API response returns empty list."""
    a = TheOddsApiAdapter.__new__(TheOddsApiAdapter)
    a._base = "https://api.the-odds-api.com/v4"
    a._key = "test-key"
    monkeypatch.setattr(a, "_get", lambda url, params: [])
    assert a.fetch_outrights() == []
