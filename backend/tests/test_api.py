"""Integration tests for all read endpoints (Tasks 16 + 17)."""
from __future__ import annotations
import pytest
from app.services.ingestion import run_refresh


@pytest.fixture()
def seeded_client(db_session, client):
    """Run a fast refresh then return the test client."""
    run_refresh(db_session, sims=400)
    return client


def test_full_api_flow(seeded_client):
    c = seeded_client

    # /meta
    r = c.get("/meta")
    assert r.status_code == 200
    data = r.json()
    assert "risk" in data
    assert "odds_formats" in data
    assert set(data["odds_formats"]) == {"decimal", "american", "fractional"}

    # /outright — 48 rows (or at least all teams that had ratings)
    r = c.get("/outright")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 48
    # Sorted by model desc
    models = [row["model"] for row in rows]
    assert models == sorted(models, reverse=True)
    # Each row has enrichment fields
    assert "name" in rows[0]
    assert "group" in rows[0]
    assert "colors" in rows[0]

    # /matches — at least 8 fixtures
    r = c.get("/matches")
    assert r.status_code == 200
    matches = r.json()
    assert len(matches) >= 8
    m = matches[0]
    assert "homeName" in m
    assert "awayName" in m

    # /matches/{id} — first match detail
    mid = matches[0]["id"]
    r = c.get(f"/matches/{mid}")
    assert r.status_code == 200
    detail = r.json()
    assert "h2h" in detail
    assert "legs" in detail

    # /matches/{id} 404
    r = c.get("/matches/nonexistent")
    assert r.status_code == 404

    # /groups — 12 groups
    r = c.get("/groups")
    assert r.status_code == 200
    groups = r.json()
    assert len(groups) == 12
    g = groups[0]
    assert "letter" in g
    assert "rows" in g
    row = g["rows"][0]
    assert "gwProb" in row
    assert "qualProb" in row
    assert "gwMarket" in row
    assert "qualMarket" in row
    assert "projRank" in row

    # /bracket — 5 rounds
    r = c.get("/bracket")
    assert r.status_code == 200
    bracket = r.json()
    assert "rounds" in bracket
    assert len(bracket["rounds"]) == 5
    assert "champion" in bracket
    assert bracket["champion"] is not None
    assert "code" in bracket["champion"]

    # /news/ESP
    r = c.get("/news/ESP")
    assert r.status_code == 200
    news = r.json()
    assert isinstance(news, list)


def test_teams_endpoints(seeded_client):
    c = seeded_client

    # /teams
    r = c.get("/teams")
    assert r.status_code == 200
    teams = r.json()
    assert len(teams) == 48
    t = teams[0]
    assert "code" in t
    assert "str" in t
    assert "elo" in t

    # /teams/ESP
    r = c.get("/teams/ESP")
    assert r.status_code == 200
    team = r.json()
    assert team["code"] == "ESP"
    assert "squad" in team
    assert len(team["squad"]) > 0
    assert "outright" in team
    assert "news" in team

    # /teams/NOTEXIST 404
    r = c.get("/teams/NOTEXIST")
    assert r.status_code == 404


def test_players_endpoints(seeded_client):
    c = seeded_client

    # GET /players?code=ESP — list players for ESP
    r = c.get("/players?code=ESP")
    assert r.status_code == 200
    players = r.json()
    assert len(players) > 0
    p = players[0]
    assert "id" in p
    assert "name" in p
    assert "pos" in p
    assert "number" in p

    # GET /players/{id}
    player_id = players[0]["id"]
    r = c.get(f"/players/{player_id}")
    assert r.status_code == 200
    detail = r.json()
    assert detail["id"] == player_id
    assert "props" in detail
    props = detail["props"]
    assert "scorer" in props or "card" in props

    # 404
    r = c.get("/players/999999")
    assert r.status_code == 404


def test_bracket_rounds(seeded_client):
    c = seeded_client
    r = c.get("/bracket")
    assert r.status_code == 200
    data = r.json()
    assert len(data["rounds"]) == 5
    round_names = [rd["name"] for rd in data["rounds"]]
    assert "Round of 32" in round_names
    assert "Final" in round_names
