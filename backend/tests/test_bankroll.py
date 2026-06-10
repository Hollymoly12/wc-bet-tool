"""Bankroll & bets endpoint tests (Task 18)."""
from __future__ import annotations
import pytest
from app.services.ingestion import run_refresh


@pytest.fixture()
def c(db_session, client):
    """Client with a seeded DB."""
    run_refresh(db_session, sims=400)
    return client


def test_bankroll_empty(c):
    r = c.get("/bankroll")
    assert r.status_code == 200
    data = r.json()
    assert data["balance"] == 1000.0
    assert data["start"] == 1000.0
    assert data["open_bets"] == []
    assert data["settled_bets"] == []


def test_place_bet(c):
    payload = {"key": "m:m1:home", "pick": "ESP to win", "team": "ESP",
               "market": "1x2", "stake": 50.0, "dec": 1.75}
    r = c.post("/bankroll/bets", json=payload)
    assert r.status_code == 201
    bet = r.json()
    assert bet["status"] == "open"
    assert bet["stake"] == 50.0
    assert bet["dec"] == 1.75
    assert bet["id"] is not None

    # bankroll shows open bet
    r2 = c.get("/bankroll")
    data = r2.json()
    assert len(data["open_bets"]) == 1
    # balance unchanged (no settled pnl)
    assert data["balance"] == 1000.0


def test_settle_won(c):
    payload = {"key": "m:m1:home", "pick": "ESP win", "team": "ESP",
               "market": "1x2", "stake": 100.0, "dec": 2.0}
    r = c.post("/bankroll/bets", json=payload)
    bet_id = r.json()["id"]

    r2 = c.post(f"/bankroll/bets/{bet_id}/settle", json={"result": "won"})
    assert r2.status_code == 200
    settled = r2.json()
    assert settled["status"] == "won"
    assert settled["pnl"] == pytest.approx(100.0)

    r3 = c.get("/bankroll")
    data = r3.json()
    assert data["balance"] == pytest.approx(1100.0)
    assert len(data["settled_bets"]) == 1


def test_settle_lost(c):
    payload = {"key": "m:m1:draw", "pick": "draw", "team": "",
               "market": "1x2", "stake": 50.0, "dec": 3.5}
    r = c.post("/bankroll/bets", json=payload)
    bet_id = r.json()["id"]

    r2 = c.post(f"/bankroll/bets/{bet_id}/settle", json={"result": "lost"})
    assert r2.status_code == 200
    settled = r2.json()
    assert settled["pnl"] == pytest.approx(-50.0)
    assert settled["status"] == "lost"

    r3 = c.get("/bankroll")
    assert r3.json()["balance"] == pytest.approx(950.0)


def test_settle_void(c):
    payload = {"key": "m:m1:void", "pick": "void test", "team": "",
               "market": "1x2", "stake": 50.0, "dec": 2.0}
    r = c.post("/bankroll/bets", json=payload)
    bet_id = r.json()["id"]

    r2 = c.post(f"/bankroll/bets/{bet_id}/settle", json={"result": "void"})
    assert r2.status_code == 200
    assert r2.json()["pnl"] == pytest.approx(0.0)
    assert r2.json()["status"] == "void"

    r3 = c.get("/bankroll")
    assert r3.json()["balance"] == pytest.approx(1000.0)


def test_delete_open_bet(c):
    payload = {"key": "m:m2:away", "pick": "NGA to win", "team": "NGA",
               "market": "1x2", "stake": 20.0, "dec": 5.0}
    r = c.post("/bankroll/bets", json=payload)
    bet_id = r.json()["id"]

    r2 = c.delete(f"/bankroll/bets/{bet_id}")
    assert r2.status_code == 204

    r3 = c.get("/bankroll")
    assert r3.json()["open_bets"] == []


def test_delete_settled_bet_fails(c):
    payload = {"key": "m:m3:home", "pick": "ENG to win", "team": "ENG",
               "market": "1x2", "stake": 30.0, "dec": 1.9}
    r = c.post("/bankroll/bets", json=payload)
    bet_id = r.json()["id"]
    c.post(f"/bankroll/bets/{bet_id}/settle", json={"result": "won"})

    r2 = c.delete(f"/bankroll/bets/{bet_id}")
    assert r2.status_code == 404


def test_settle_invalid_result(c):
    payload = {"key": "m:m4:home", "pick": "BRA win", "team": "BRA",
               "market": "1x2", "stake": 25.0, "dec": 1.6}
    r = c.post("/bankroll/bets", json=payload)
    bet_id = r.json()["id"]

    r2 = c.post(f"/bankroll/bets/{bet_id}/settle", json={"result": "invalid"})
    assert r2.status_code == 422


def test_settle_nonexistent(c):
    r = c.post("/bankroll/bets/999999/settle", json={"result": "won"})
    assert r.status_code == 404
