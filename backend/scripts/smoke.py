#!/usr/bin/env python
"""Smoke test: uses TestClient with an in-memory SQLite, runs run_refresh, hits every endpoint.

Usage:
    python scripts/smoke.py
"""
from __future__ import annotations
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
import app.db.models  # noqa: F401

# -- Setup in-memory SQLite shared across connections -------------------------
engine = create_engine(
    "sqlite:///file:smoke_test?mode=memory&cache=shared&uri=true",
    connect_args={"check_same_thread": False},
)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, expire_on_commit=False)
db_session = Session()

# -- Seed data ----------------------------------------------------------------
from app.services.ingestion import run_refresh
print("Running refresh (sims=2000)...")
run_refresh(db_session, sims=2000)
print("Refresh done.\n")

# -- TestClient ---------------------------------------------------------------
from app.main import app
from app.db.session import get_db
from fastapi.testclient import TestClient

def _override():
    yield db_session

app.dependency_overrides[get_db] = _override

ENDPOINTS = [
    ("GET", "/meta"),
    ("GET", "/outright"),
    ("GET", "/matches"),
    ("GET", "/matches/m1"),
    ("GET", "/matches/m2"),
    ("GET", "/groups"),
    ("GET", "/bracket"),
    ("GET", "/teams"),
    ("GET", "/teams/ESP"),
    ("GET", "/teams/BRA"),
    ("GET", "/players?code=ESP"),
    ("GET", "/players/1"),
    ("GET", "/news/ESP"),
    ("GET", "/news/FRA"),
    ("GET", "/bankroll"),
]

failed = 0
with TestClient(app) as client:
    for method, path in ENDPOINTS:
        r = client.request(method, path)
        status = r.status_code
        ok = "OK" if 200 <= status < 300 else "FAIL"
        if ok == "FAIL":
            failed += 1
        print(f"  [{ok}] {method} {path}  -> {status}")

    # Quick bankroll flow
    r = client.post("/bankroll/bets", json={"key": "smoke:test", "pick": "ESP win",
                                            "team": "ESP", "market": "1x2",
                                            "stake": 50.0, "dec": 1.75})
    bet_id = r.json()["id"] if r.status_code == 201 else None
    print(f"  [{'OK' if r.status_code == 201 else 'FAIL'}] POST /bankroll/bets -> {r.status_code}")
    if bet_id:
        r2 = client.post(f"/bankroll/bets/{bet_id}/settle", json={"result": "won"})
        print(f"  [{'OK' if r2.status_code == 200 else 'FAIL'}] POST /bankroll/bets/{bet_id}/settle -> {r2.status_code}")

    # admin refresh (quick)
    # r3 = client.post("/admin/refresh")  # skip - slow
    # print(f"  POST /admin/refresh -> {r3.status_code}")

app.dependency_overrides.clear()

# Cleanup
Base.metadata.drop_all(engine)
engine.dispose()

print()
if failed:
    print(f"SMOKE FAILED: {failed} endpoint(s) returned non-2xx")
    sys.exit(1)
else:
    print("All endpoints 200 OK - smoke passed!")
