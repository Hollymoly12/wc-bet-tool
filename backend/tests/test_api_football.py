"""Tests for ApiFootballAdapter and InjuriesNewsProvider.

All HTTP calls are monkeypatched via the internal _get() helpers.
"""
from __future__ import annotations

import pytest

from app.providers.api_football import ApiFootballAdapter
from app.providers.injuries import InjuriesNewsProvider

# ---------------------------------------------------------------------------
# Sample fixture payload (1 upcoming match: Spain vs Croatia)
# ---------------------------------------------------------------------------
SAMPLE_FIXTURES_RESPONSE = {
    "response": [
        {
            "fixture": {
                "id": 100001,
                "date": "2026-06-13T18:00:00+00:00",
                "status": {"short": "NS"},
                "venue": {"name": "Mercedes-Benz Stadium", "city": "Atlanta"},
            },
            "league": {
                "id": 1,
                "name": "FIFA World Cup",
                "season": 2026,
                "round": "Group Stage - 1",
            },
            "teams": {
                "home": {"id": 9, "name": "Spain"},
                "away": {"id": 3, "name": "Croatia"},
            },
            "goals": {"home": None, "away": None},
        }
    ]
}

# ---------------------------------------------------------------------------
# Sample FT result payload (Spain beat Croatia 2-1)
# ---------------------------------------------------------------------------
SAMPLE_RESULTS_RESPONSE = {
    "response": [
        {
            "fixture": {
                "id": 100001,
                "date": "2026-06-13T18:00:00+00:00",
                "status": {"short": "FT"},
                "venue": {"name": "Mercedes-Benz Stadium"},
            },
            "league": {
                "id": 1,
                "name": "FIFA World Cup",
                "season": 2026,
                "round": "Group Stage - 1",
            },
            "teams": {
                "home": {"id": 9, "name": "Spain"},
                "away": {"id": 3, "name": "Croatia"},
            },
            "goals": {"home": 2, "away": 1},
        }
    ]
}

# ---------------------------------------------------------------------------
# Sample injuries payload
# ---------------------------------------------------------------------------
SAMPLE_INJURIES_RESPONSE = {
    "response": [
        {
            "player": {"id": 754, "name": "Pedri", "photo": ""},
            "team": {"id": 9, "name": "Spain"},
            "fixture": {"id": 100001},
            "reason": "Hamstring injury",
            "type": "Injury",
        },
        {
            "player": {"id": 284629, "name": "Luka Modrić", "photo": ""},
            "team": {"id": 3, "name": "Croatia"},
            "fixture": {"id": 100001},
            "reason": "Suspended - accumulated yellow cards",
            "type": "Suspension",
        },
    ]
}


# ---------------------------------------------------------------------------
# Fixtures adapter tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def football_adapter(monkeypatch):
    a = ApiFootballAdapter.__new__(ApiFootballAdapter)
    a._base = "https://v3.football.api-sports.io"
    a._key = "test-key"
    return a


def test_fetch_fixtures_count(football_adapter, monkeypatch):
    monkeypatch.setattr(football_adapter, "_get", lambda url, params: SAMPLE_FIXTURES_RESPONSE)
    fixtures = football_adapter.fetch_fixtures()
    assert len(fixtures) == 1


def test_fetch_fixtures_id(football_adapter, monkeypatch):
    """Fixture id must follow the home_code_away_code convention."""
    monkeypatch.setattr(football_adapter, "_get", lambda url, params: SAMPLE_FIXTURES_RESPONSE)
    fixtures = football_adapter.fetch_fixtures()
    assert fixtures[0].id == "ESP_CRO"


def test_fetch_fixtures_teams(football_adapter, monkeypatch):
    monkeypatch.setattr(football_adapter, "_get", lambda url, params: SAMPLE_FIXTURES_RESPONSE)
    fx = football_adapter.fetch_fixtures()[0]
    assert fx.home == "ESP"
    assert fx.away == "CRO"


def test_fetch_fixtures_kickoff(football_adapter, monkeypatch):
    """Kickoff must be a timezone-aware UTC datetime."""
    from datetime import timezone
    monkeypatch.setattr(football_adapter, "_get", lambda url, params: SAMPLE_FIXTURES_RESPONSE)
    fx = football_adapter.fetch_fixtures()[0]
    assert fx.kickoff is not None
    assert fx.kickoff.tzinfo == timezone.utc


def test_fetch_fixtures_venue(football_adapter, monkeypatch):
    monkeypatch.setattr(football_adapter, "_get", lambda url, params: SAMPLE_FIXTURES_RESPONSE)
    fx = football_adapter.fetch_fixtures()[0]
    assert "Mercedes" in fx.venue


def test_fetch_fixtures_unknown_team_skipped(football_adapter, monkeypatch):
    """Fixtures with unresolvable team names are dropped."""
    bad = {
        "response": [
            {
                "fixture": {"id": 999, "date": "2026-01-01T00:00:00+00:00",
                            "venue": {"name": ""}},
                "league": {"round": ""},
                "teams": {
                    "home": {"name": "Atlantis FC"},
                    "away": {"name": "Spain"},
                },
                "goals": {"home": None, "away": None},
            }
        ]
    }
    monkeypatch.setattr(football_adapter, "_get", lambda url, params: bad)
    assert football_adapter.fetch_fixtures() == []


# ---------------------------------------------------------------------------
# Results adapter tests
# ---------------------------------------------------------------------------

def test_fetch_results_count(football_adapter, monkeypatch):
    monkeypatch.setattr(football_adapter, "_get", lambda url, params: SAMPLE_RESULTS_RESPONSE)
    results = football_adapter.fetch_results()
    assert len(results) == 1


def test_fetch_results_goals(football_adapter, monkeypatch):
    monkeypatch.setattr(football_adapter, "_get", lambda url, params: SAMPLE_RESULTS_RESPONSE)
    r = football_adapter.fetch_results()[0]
    assert r.home == "ESP"
    assert r.away == "CRO"
    assert r.home_goals == 2
    assert r.away_goals == 1


def test_fetch_results_competition(football_adapter, monkeypatch):
    monkeypatch.setattr(football_adapter, "_get", lambda url, params: SAMPLE_RESULTS_RESPONSE)
    r = football_adapter.fetch_results()[0]
    assert r.competition == "WC2026"


def test_fetch_results_days_ago_is_float(football_adapter, monkeypatch):
    """days_ago must be a float (positive for past matches, may be negative for future dates in tests)."""
    monkeypatch.setattr(football_adapter, "_get", lambda url, params: SAMPLE_RESULTS_RESPONSE)
    r = football_adapter.fetch_results()[0]
    assert isinstance(r.days_ago, float)


# ---------------------------------------------------------------------------
# Squads — should return seed data (not empty)
# ---------------------------------------------------------------------------

def test_fetch_squads_returns_seed_data(football_adapter):
    from app.seed import seed_data
    squads = football_adapter.fetch_squads()
    assert squads is seed_data.SQUADS
    assert "ESP" in squads


# ---------------------------------------------------------------------------
# Injuries adapter tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def injuries_adapter(monkeypatch):
    a = InjuriesNewsProvider.__new__(InjuriesNewsProvider)
    a._base = "https://v3.football.api-sports.io"
    a._key = "test-key"
    return a


def test_injuries_count(injuries_adapter, monkeypatch):
    monkeypatch.setattr(injuries_adapter, "_get", lambda url, params: SAMPLE_INJURIES_RESPONSE)
    items = injuries_adapter.fetch_news()
    assert len(items) == 2


def test_injuries_code_resolved(injuries_adapter, monkeypatch):
    monkeypatch.setattr(injuries_adapter, "_get", lambda url, params: SAMPLE_INJURIES_RESPONSE)
    items = injuries_adapter.fetch_news()
    codes = {i.code for i in items}
    assert "ESP" in codes
    assert "CRO" in codes


def test_injuries_tag_injury(injuries_adapter, monkeypatch):
    monkeypatch.setattr(injuries_adapter, "_get", lambda url, params: SAMPLE_INJURIES_RESPONSE)
    items = injuries_adapter.fetch_news()
    spain_item = next(i for i in items if i.code == "ESP")
    assert spain_item.tag == "injury"


def test_injuries_tag_suspension(injuries_adapter, monkeypatch):
    monkeypatch.setattr(injuries_adapter, "_get", lambda url, params: SAMPLE_INJURIES_RESPONSE)
    items = injuries_adapter.fetch_news()
    cro_item = next(i for i in items if i.code == "CRO")
    assert cro_item.tag == "susp"


def test_injuries_source(injuries_adapter, monkeypatch):
    monkeypatch.setattr(injuries_adapter, "_get", lambda url, params: SAMPLE_INJURIES_RESPONSE)
    items = injuries_adapter.fetch_news()
    assert all(i.source == "API-Football" for i in items)


def test_injuries_text_contains_player(injuries_adapter, monkeypatch):
    monkeypatch.setattr(injuries_adapter, "_get", lambda url, params: SAMPLE_INJURIES_RESPONSE)
    items = injuries_adapter.fetch_news()
    spain_item = next(i for i in items if i.code == "ESP")
    assert "Pedri" in spain_item.text


def test_injuries_unknown_team_skipped(injuries_adapter, monkeypatch):
    bad = {
        "response": [
            {
                "player": {"name": "John Doe"},
                "team": {"name": "Atlantis FC"},
                "reason": "Knee",
                "type": "Injury",
            }
        ]
    }
    monkeypatch.setattr(injuries_adapter, "_get", lambda url, params: bad)
    assert injuries_adapter.fetch_news() == []
