# WC Bet Tool Back-end Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI + PostgreSQL back-end with an independent statistical betting model (ratings → Dixon-Coles → Monte-Carlo) that fully runs and is tested on seed data with no API keys, then layers real data (The Odds API, API-Football, RSS) via env keys.

**Architecture:** Pure, testable algo modules (`app/models/`) take numbers in and probabilities out. Services wire providers + DB + models. Providers sit behind interfaces with real adapters and Seed fallbacks selected by env. Approach B: a refresh pipeline computes and persists snapshots; the API serves snapshots fast; bets/bankroll are real-time.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic, PostgreSQL, Pydantic v2, httpx, feedparser, numpy/scipy, pytest, ruff.

---

## File Structure

```
backend/
  pyproject.toml          # deps + tool config (ruff, pytest)
  .env.example            # ODDS_API_KEY, API_FOOTBALL_KEY, DATABASE_URL
  README.md               # run/test steps
  alembic.ini, alembic/   # migrations
  app/
    main.py               # FastAPI app + router registration + CORS
    config.py             # pydantic-settings Settings
    cli.py                # `python -m app.cli refresh|seed-db`
    db/
      base.py             # DeclarativeBase
      session.py          # engine, SessionLocal, get_db
      models.py           # ORM tables
    models/               # ALGO CORE (pure)
      poisson.py          # pmf/cdf helpers
      betting.py          # devig, ev, kelly, stake, verdict
      ratings.py          # Dixon-Coles MLE + Elo
      match_model.py      # score matrix -> markets
      player_props.py     # player Poisson props
      tournament.py       # Monte-Carlo groups + KO
    providers/
      base.py             # Protocols + DTOs
      factory.py          # env-based selection w/ seed fallback
      cache.py            # DB cache + rate-limit
      the_odds_api.py     # OddsProvider real
      api_football.py     # FootballProvider real
      injuries.py         # NewsProvider (API-Football injuries)
      rss_news.py         # NewsProvider (RSS)
      seed/
        __init__.py
        seed_data.py      # ported prototype data (teams, matches, squads, history)
        seed_odds.py      # SeedOddsProvider
        seed_football.py  # SeedFootballProvider
        seed_news.py      # SeedNewsProvider
    services/
      ingestion.py        # fetch + persist
      pricing.py          # orchestrate model -> model_snapshots
      tournament_service.py # run sim -> tournament_snapshot
      bankroll.py         # bets + ledger
      news.py             # news refresh
    schemas/              # Pydantic response models (frontend shape)
      outright.py matches.py groups.py bracket.py teams.py players.py bankroll.py news.py meta.py
    api/
      deps.py
      routes_outright.py routes_matches.py routes_groups.py routes_bracket.py
      routes_teams.py routes_players.py routes_news.py routes_bankroll.py
      routes_meta.py routes_admin.py
  tests/
    test_poisson.py test_betting.py test_ratings.py test_match_model.py
    test_player_props.py test_tournament.py test_pricing.py
    test_bankroll.py test_api.py conftest.py
```

---

## PHASE 1 — Foundations

### Task 1: Project scaffold & config

**Files:**
- Create: `backend/pyproject.toml`, `backend/.env.example`, `backend/app/__init__.py`, `backend/app/config.py`, `backend/tests/__init__.py`

- [ ] **Step 1: Create `backend/pyproject.toml`**

```toml
[project]
name = "wc-bet-tool-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.110", "uvicorn[standard]>=0.29", "sqlalchemy>=2.0",
  "alembic>=1.13", "psycopg[binary]>=3.1", "pydantic>=2.6",
  "pydantic-settings>=2.2", "httpx>=0.27", "feedparser>=6.0",
  "numpy>=1.26", "scipy>=1.12", "python-dateutil>=2.9",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23", "ruff>=0.4"]

[tool.pytest.ini_options]
pythonpath = ["."]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **Step 2: Create `backend/.env.example`**

```bash
DATABASE_URL=postgresql+psycopg://wc:wc@localhost:5432/wcbet
ODDS_API_KEY=
API_FOOTBALL_KEY=
ODDS_API_BASE=https://api.the-odds-api.com/v4
API_FOOTBALL_BASE=https://v3.football.api-sports.io
MODEL_SIMS=50000
MODEL_DECAY_HALFLIFE_DAYS=540
```

- [ ] **Step 3: Create `backend/app/config.py`**

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://wc:wc@localhost:5432/wcbet"
    odds_api_key: str = ""
    api_football_key: str = ""
    odds_api_base: str = "https://api.the-odds-api.com/v4"
    api_football_base: str = "https://v3.football.api-sports.io"
    model_sims: int = 50000
    model_decay_halflife_days: int = 540

    @property
    def has_odds_key(self) -> bool:
        return bool(self.odds_api_key.strip())

    @property
    def has_football_key(self) -> bool:
        return bool(self.api_football_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Create empty `backend/app/__init__.py` and `backend/tests/__init__.py`**

- [ ] **Step 5: Commit**

```bash
cd backend && git add -A && git commit -m "chore: project scaffold and settings"
```

---

### Task 2: Poisson math helpers (TDD)

**Files:**
- Create: `backend/app/models/__init__.py`, `backend/app/models/poisson.py`
- Test: `backend/tests/test_poisson.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_poisson.py
import math
from app.models.poisson import pmf, cdf, tail_ge

def test_pmf_matches_formula():
    assert pmf(0, 2.0) == math.exp(-2.0)
    assert abs(pmf(2, 2.0) - (math.exp(-2.0) * 4 / 2)) < 1e-12

def test_cdf_is_cumulative():
    mu = 1.7
    assert abs(cdf(0, mu) - pmf(0, mu)) < 1e-12
    assert abs(cdf(3, mu) - sum(pmf(k, mu) for k in range(4))) < 1e-12

def test_tail_ge_complement():
    mu = 2.3
    assert abs(tail_ge(1, mu) - (1 - pmf(0, mu))) < 1e-12
    # over 2.5 == P(>=3) == 1 - cdf(2)
    assert abs(tail_ge(3, mu) - (1 - cdf(2, mu))) < 1e-12
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_poisson.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Write `backend/app/models/poisson.py`**

```python
"""Poisson probability helpers used across the betting models."""
import math


def pmf(k: int, mu: float) -> float:
    """P(X = k) for X ~ Poisson(mu)."""
    if k < 0:
        return 0.0
    return math.exp(-mu) * mu**k / math.factorial(k)


def cdf(n: int, mu: float) -> float:
    """P(X <= n)."""
    return sum(pmf(k, mu) for k in range(max(0, n) + 1))


def tail_ge(n: int, mu: float) -> float:
    """P(X >= n)."""
    if n <= 0:
        return 1.0
    return 1.0 - cdf(n - 1, mu)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_poisson.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend && git add -A && git commit -m "feat: poisson math helpers"
```

---

### Task 3: Betting math — devig, EV, Kelly, stake, verdict (TDD)

**Files:**
- Create: `backend/app/models/betting.py`
- Test: `backend/tests/test_betting.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_betting.py
from app.models import betting as B

def test_implied_and_ev():
    assert abs(B.implied_prob(2.0) - 0.5) < 1e-12
    assert abs(B.ev(0.6, 2.0) - 0.2) < 1e-12   # 0.6*2 - 1

def test_kelly_full_and_zero_floor():
    # p=0.6 dec=2.0 -> b=1 -> (1*0.6-0.4)/1 = 0.2
    assert abs(B.kelly_full(0.6, 2.0) - 0.2) < 1e-12
    # no edge -> non-positive kelly floored at 0
    assert B.kelly_full(0.4, 2.0) == 0.0

def test_devig_multiplicative_sums_to_one():
    fair = B.devig_multiplicative([1/0.5, 1/0.3, 1/0.25])  # overround book
    assert abs(sum(fair) - 1.0) < 1e-9
    assert fair[0] > fair[1] > fair[2]

def test_devig_shin_sums_to_one_and_reduces_favorite_bias():
    odds = [1.5, 4.2, 7.0]
    fair = B.devig_shin(odds)
    assert abs(sum(fair) - 1.0) < 1e-6
    # all in (0,1)
    assert all(0 < p < 1 for p in fair)

def test_recommended_stake_caps_and_rounds():
    # huge kelly should be capped by profile cap, rounded to 5
    stake = B.recommended_stake(p=0.9, dec=3.0, bankroll=1000, risk="conservative")
    assert stake % 5 == 0
    assert stake <= 1000 * 0.04  # conservative cap

def test_verdict_thresholds():
    assert B.verdict(0.12) == "strong"
    assert B.verdict(0.05) == "value"
    assert B.verdict(0.0) == "pass"
    assert B.verdict(-0.05) == "avoid"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_betting.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Write `backend/app/models/betting.py`**

```python
"""Core betting math: pricing, de-vigging, staking, value verdicts."""
from __future__ import annotations

RISK = {
    "conservative": {"label": "Conservative", "mult": 0.25, "cap": 0.04},
    "balanced": {"label": "Balanced", "mult": 0.50, "cap": 0.07},
    "aggressive": {"label": "Aggressive", "mult": 1.00, "cap": 0.12},
}


def implied_prob(dec: float) -> float:
    return 1.0 / dec


def ev(p: float, dec: float) -> float:
    """Expected value per unit staked."""
    return p * dec - 1.0


def kelly_full(p: float, dec: float) -> float:
    b = dec - 1.0
    if b <= 0:
        return 0.0
    f = (b * p - (1 - p)) / b
    return max(0.0, f)


def devig_multiplicative(dec_odds: list[float]) -> list[float]:
    """Normalize raw implied probabilities so they sum to 1."""
    raw = [1.0 / d for d in dec_odds]
    s = sum(raw)
    return [r / s for r in raw]


def devig_shin(dec_odds: list[float], iters: int = 60) -> list[float]:
    """Shin (1992) de-vig: solves for insider-trading proportion z, returns fair probs."""
    pi = [1.0 / d for d in dec_odds]
    booksum = sum(pi)
    z = 0.0
    for _ in range(iters):
        denom = sum(((zi := (z * z + 4 * (1 - z) * (p**2) / booksum)) ** 0.5) for p in pi)
        z_new = (denom - 2) / (len(pi) - 2) if len(pi) > 2 else 0.0
        if abs(z_new - z) < 1e-12:
            z = z_new
            break
        z = max(0.0, min(0.2, z_new))
    fair = []
    for p in pi:
        val = ((z * z + 4 * (1 - z) * (p**2) / booksum) ** 0.5 - z) / (2 * (1 - z))
        fair.append(val)
    s = sum(fair)
    return [f / s for f in fair]


def fair_probs(dec_odds: list[float], method: str = "shin") -> list[float]:
    if method == "shin" and len(dec_odds) >= 2:
        try:
            return devig_shin(dec_odds)
        except (ValueError, ZeroDivisionError):
            return devig_multiplicative(dec_odds)
    return devig_multiplicative(dec_odds)


def recommended_stake(p: float, dec: float, bankroll: float, risk: str = "balanced") -> int:
    r = RISK.get(risk, RISK["balanced"])
    f = min(kelly_full(p, dec) * r["mult"], r["cap"])
    return int(round((bankroll * f) / 5.0)) * 5


def verdict(edge: float) -> str:
    """edge = p_model - p_fair."""
    if edge >= 0.10:
        return "strong"
    if edge >= 0.03:
        return "value"
    if edge >= -0.01:
        return "pass"
    return "avoid"


def confidence(model_prob: float, coverage: float = 1.0) -> int:
    """0-100 confidence from distance-from-coinflip and data coverage."""
    sharpness = abs(model_prob - 0.5) * 2  # 0..1
    return int(round(max(0.0, min(1.0, 0.45 + 0.45 * sharpness)) * coverage * 100))
```

- [ ] **Step 4: Run test to verify it passes** (fix Shin numerics if a test fails — Shin must satisfy sum≈1; if `devig_shin` diverges, clamp z and re-normalize, which the code already does).

Run: `cd backend && pytest tests/test_betting.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend && git add -A && git commit -m "feat: betting math (devig, ev, kelly, stake, verdict)"
```

---

### Task 4: DB layer — base, session, ORM models

**Files:**
- Create: `backend/app/db/__init__.py`, `backend/app/db/base.py`, `backend/app/db/session.py`, `backend/app/db/models.py`

- [ ] **Step 1: Create `backend/app/db/base.py`**

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

- [ ] **Step 2: Create `backend/app/db/session.py`**

```python
from collections.abc import Iterator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: Create `backend/app/db/models.py`** (full ORM per spec §5)

```python
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Team(Base):
    __tablename__ = "teams"
    code: Mapped[str] = mapped_column(String(4), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    group: Mapped[str] = mapped_column(String(2))
    colors: Mapped[list] = mapped_column(JSON, default=list)
    elo: Mapped[float] = mapped_column(Float, default=1500.0)
    attack: Mapped[float] = mapped_column(Float, default=0.0)
    defense: Mapped[float] = mapped_column(Float, default=0.0)
    str_rating: Mapped[float] = mapped_column(Float, default=55.0)
    form: Mapped[str] = mapped_column(String(8), default="")


class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(4), index=True)
    number: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(64))
    pos: Mapped[str] = mapped_column(String(4))
    club: Mapped[str] = mapped_column(String(48), default="")
    tier: Mapped[float] = mapped_column(Float, default=1.0)
    starter: Mapped[bool] = mapped_column(default=False)
    rates: Mapped[dict] = mapped_column(JSON, default=dict)


class Match(Base):
    __tablename__ = "matches"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    home: Mapped[str] = mapped_column(String(4))
    away: Mapped[str] = mapped_column(String(4))
    group: Mapped[str] = mapped_column(String(2), default="")
    stage: Mapped[str] = mapped_column(String(24), default="group")
    kickoff: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    venue: Mapped[str] = mapped_column(String(96), default="")


class MatchResult(Base):
    __tablename__ = "match_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime)
    home: Mapped[str] = mapped_column(String(4))
    away: Mapped[str] = mapped_column(String(4))
    home_goals: Mapped[int] = mapped_column(Integer)
    away_goals: Mapped[int] = mapped_column(Integer)
    competition: Mapped[str] = mapped_column(String(48), default="")
    weight: Mapped[float] = mapped_column(Float, default=1.0)


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_key: Mapped[str] = mapped_column(String(64), index=True)
    book: Mapped[str] = mapped_column(String(48))
    selection: Mapped[str] = mapped_column(String(64))
    dec: Mapped[float] = mapped_column(Float)
    captured_at: Mapped[datetime] = mapped_column(DateTime)


class ModelSnapshot(Base):
    __tablename__ = "model_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(24), index=True)  # outright|match|group|player
    ref: Mapped[str] = mapped_column(String(48), index=True)   # team code or match id
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class TournamentSnapshot(Base):
    __tablename__ = "tournament_snapshot"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class TeamNews(Base):
    __tablename__ = "team_news"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(4), index=True)
    tag: Mapped[str] = mapped_column(String(12))
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(48), default="")
    url: Mapped[str] = mapped_column(String(256), default="")
    published_at: Mapped[datetime] = mapped_column(DateTime)


class Bet(Base):
    __tablename__ = "bets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(96))
    pick: Mapped[str] = mapped_column(String(128))
    team: Mapped[str] = mapped_column(String(4), default="")
    market: Mapped[str] = mapped_column(String(48), default="")
    stake: Mapped[float] = mapped_column(Float)
    dec: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(8), default="open")  # open|won|lost|void
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    placed_at: Mapped[datetime] = mapped_column(DateTime)


class BankrollTxn(Base):
    __tablename__ = "bankroll_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(16))  # deposit|bet|settle
    amount: Mapped[float] = mapped_column(Float)
    bet_id: Mapped[int | None] = mapped_column(ForeignKey("bets.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class ProviderCall(Base):
    __tablename__ = "provider_calls"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(32))
    endpoint: Mapped[str] = mapped_column(String(96))
    called_at: Mapped[datetime] = mapped_column(DateTime)
```

- [ ] **Step 4: Create `backend/app/db/__init__.py`** (empty)

- [ ] **Step 5: Commit**

```bash
cd backend && git add -A && git commit -m "feat: db base, session, ORM models"
```

---

### Task 5: Alembic migrations + test DB config (SQLite for tests)

**Files:**
- Create: `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako`, `backend/tests/conftest.py`

- [ ] **Step 1: Init alembic**

Run: `cd backend && alembic init alembic` then set `alembic/env.py` `target_metadata = Base.metadata` (import `from app.db.base import Base` and `import app.db.models`), and read URL from `get_settings().database_url`.

- [ ] **Step 2: Generate initial migration**

Run: `cd backend && alembic revision --autogenerate -m "init schema"` (requires a reachable Postgres). Expected: a versions file creating all tables.

- [ ] **Step 3: Create `backend/tests/conftest.py`** — in-memory SQLite session + FastAPI client override so tests need **no Postgres**.

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.base import Base
import app.db.models  # noqa: F401  (register tables)

@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    s = TestingSession()
    try:
        yield s
    finally:
        s.close()

@pytest.fixture()
def client(db_session):
    from app.main import app
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: iter([db_session])
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 4: Commit**

```bash
cd backend && git add -A && git commit -m "feat: alembic setup + sqlite test fixtures"
```

---

### Task 6: Seed data port (prototype → Python)

**Files:**
- Create: `backend/app/seed/__init__.py`, `backend/app/seed/seed_data.py`

Port the prototype's `rawTeams` (48), `rawMatches` (8), `GOALS`, squads (`WC_SQUADS` from `squads.js`/`squads2.js`), and a synthetic historical-results generator for calibration.

- [ ] **Step 1: Create `backend/app/seed/seed_data.py`** with `TEAMS`, `MATCHES`, `GOALS`, `SQUADS`, `NAMES`, `COLORS`, `GROUP_LETTERS` copied from `project/data.js` + `project/squads*.js` (transcribe values verbatim — these are illustrative WC2026 data).

```python
# Transcribe from project/data.js rawTeams (code, group, dec, model, conf, form, str)
TEAMS = [
    {"code": "ARG", "group": "A", "dec": 8.0, "model": 0.135, "conf": 81, "form": "WWWWD", "str": 89},
    # ... all 48 rows ...
]
MATCHES = [
    {"id": "m1", "home": "ESP", "away": "CRO", "group": "B", "day": "Jun 13", "time": "18:00",
     "venue": "Mercedes-Benz Stadium · Atlanta", "odds": [1.62, 4.0, 5.8], "conf": 78},
    # ... all 8 ...
]
GOALS = {"m1": [1.9, 0.8], "m2": [2.2, 0.6]}  # ... all 8
NAMES = {"ESP": "Spain"}   # full map
COLORS = {"ESP": ["#C60B1E", "#FFC400"]}  # full map
GROUP_LETTERS = ["A","B","C","D","E","F","G","H","I","J","K","L"]
SQUADS = {"ESP": ["4-3-3", [[1,"Unai Simón","GK","Athletic Club"], ...]]}  # from squads*.js
```

- [ ] **Step 2: Add `synth_history(seed=42) -> list[dict]`** — generate ~12 results per team from `str` ratings via Poisson so `ratings.py` can be calibrated deterministically without a real API.

```python
import math, random
def synth_history(n_per_team: int = 12, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    codes = [t["code"] for t in TEAMS]
    strength = {t["code"]: t["str"] for t in TEAMS}
    out = []
    base = 1.35
    for _ in range(n_per_team * len(codes) // 2):
        h, a = rng.sample(codes, 2)
        lh = base * math.exp((strength[h] - 70) / 40 + 0.15)
        la = base * math.exp((strength[a] - 70) / 40)
        hg = _pois_sample(rng, lh); ag = _pois_sample(rng, la)
        out.append({"home": h, "away": a, "home_goals": hg, "away_goals": ag,
                    "days_ago": rng.randint(20, 900)})
    return out

def _pois_sample(rng, mu):
    L, k, p = math.exp(-mu), 0, 1.0
    while True:
        k += 1; p *= rng.random()
        if p <= L: return k - 1
```

- [ ] **Step 3: Commit**

```bash
cd backend && git add -A && git commit -m "feat: port prototype seed data + synthetic history"
```

> **NOTE for implementer:** Transcribe ALL 48 teams, 8 matches, full NAMES/COLORS/SQUADS maps from `project/data.js`, `project/squads.js`, `project/squads2.js`. Do not abbreviate in the real file.

---

## PHASE 2 — Model

### Task 7: Ratings — Elo + Dixon-Coles fit (TDD)

**Files:**
- Create: `backend/app/models/ratings.py`
- Test: `backend/tests/test_ratings.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_ratings.py
import math
from app.models.ratings import fit_ratings, TeamRatings

def _history():
    # ARG (strong) beats NGA (weak) repeatedly at home and away
    h = []
    for _ in range(15):
        h.append({"home": "ARG", "away": "NGA", "home_goals": 3, "away_goals": 0, "days_ago": 100})
        h.append({"home": "NGA", "away": "ARG", "home_goals": 0, "away_goals": 2, "days_ago": 100})
    return h

def test_fit_returns_ratings_per_team():
    r = fit_ratings(_history(), codes=["ARG", "NGA"], halflife_days=540)
    assert set(r.teams) == {"ARG", "NGA"}
    assert isinstance(r.teams["ARG"], TeamRatings)

def test_stronger_team_has_higher_net_rating():
    r = fit_ratings(_history(), codes=["ARG", "NGA"], halflife_days=540)
    arg = r.teams["ARG"]; nga = r.teams["NGA"]
    # net = attack - defense ; ARG should dominate
    assert (arg.attack - arg.defense) > (nga.attack - nga.defense)

def test_home_advantage_positive():
    r = fit_ratings(_history(), codes=["ARG", "NGA"], halflife_days=540)
    assert r.home_adv > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_ratings.py -v` → FAIL

- [ ] **Step 3: Write `backend/app/models/ratings.py`**

```python
"""Dixon-Coles attack/defense ratings fitted by weighted MLE, plus an Elo fallback."""
from __future__ import annotations
from dataclasses import dataclass, field
import math
import numpy as np
from scipy.optimize import minimize


@dataclass
class TeamRatings:
    attack: float
    defense: float
    elo: float = 1500.0
    str_rating: float = 55.0


@dataclass
class RatingsModel:
    teams: dict[str, TeamRatings]
    home_adv: float
    rho: float
    base: float
    idx: dict[str, int] = field(default_factory=dict)

    def lambdas(self, home: str, away: str) -> tuple[float, float]:
        th, ta = self.teams[home], self.teams[away]
        lh = math.exp(self.base + self.home_adv + th.attack - ta.defense)
        la = math.exp(self.base + ta.attack - th.defense)
        return lh, la


def _decay_weight(days_ago: float, halflife_days: float) -> float:
    return 0.5 ** (days_ago / halflife_days)


def _dc_tau(hg: int, ag: int, lh: float, la: float, rho: float) -> float:
    if hg == 0 and ag == 0:
        return 1 - lh * la * rho
    if hg == 0 and ag == 1:
        return 1 + lh * rho
    if hg == 1 and ag == 0:
        return 1 + la * rho
    if hg == 1 and ag == 1:
        return 1 - rho
    return 1.0


def fit_ratings(history: list[dict], codes: list[str], halflife_days: float = 540.0) -> RatingsModel:
    idx = {c: i for i, c in enumerate(codes)}
    n = len(codes)
    rows = [h for h in history if h["home"] in idx and h["away"] in idx]
    weights = np.array([_decay_weight(h.get("days_ago", 0), halflife_days) for h in rows])

    def unpack(params):
        atk = params[:n]
        df = params[n:2 * n]
        home_adv = params[2 * n]
        rho = params[2 * n + 1]
        base = params[2 * n + 2]
        return atk, df, home_adv, rho, base

    def neg_loglik(params):
        atk, df, home_adv, rho, base = unpack(params)
        # identifiability: center attack
        atk = atk - atk.mean()
        df = df - df.mean()
        ll = 0.0
        for w, h in zip(weights, rows):
            i, j = idx[h["home"]], idx[h["away"]]
            lh = math.exp(base + home_adv + atk[i] - df[j])
            la = math.exp(base + atk[j] - df[i])
            hg, ag = h["home_goals"], h["away_goals"]
            tau = _dc_tau(hg, ag, lh, la, rho)
            tau = max(tau, 1e-6)
            term = (-lh + hg * math.log(lh) - math.lgamma(hg + 1)
                    - la + ag * math.log(la) - math.lgamma(ag + 1) + math.log(tau))
            ll += w * term
        return -ll

    x0 = np.concatenate([np.zeros(n), np.zeros(n), [0.25, -0.05, 0.0]])
    res = minimize(neg_loglik, x0, method="L-BFGS-B",
                   bounds=[(-3, 3)] * (2 * n) + [(-0.5, 1.0), (-0.2, 0.2), (-1.0, 1.5)])
    atk, df, home_adv, rho, base = unpack(res.x)
    atk = atk - atk.mean(); df = df - df.mean()
    teams = {}
    nets = atk - df
    lo, hi = float(nets.min()), float(nets.max())
    for c in codes:
        i = idx[c]
        net = nets[i]
        strv = 50 + 45 * ((net - lo) / (hi - lo)) if hi > lo else 70.0
        teams[c] = TeamRatings(attack=float(atk[i]), defense=float(df[i]),
                               elo=1500.0 + 200 * net, str_rating=float(strv))
    return RatingsModel(teams=teams, home_adv=float(home_adv), rho=float(rho),
                        base=float(base), idx=idx)
```

- [ ] **Step 4: Run test to verify it passes** (if the optimizer is flaky on tiny data, the test history is strongly separable so the sign assertions hold).

Run: `cd backend && pytest tests/test_ratings.py -v` → PASS

- [ ] **Step 5: Commit**

```bash
cd backend && git add -A && git commit -m "feat: Dixon-Coles ratings fit + Elo strength"
```

---

### Task 8: Match model — score matrix → all markets (TDD)

**Files:**
- Create: `backend/app/models/match_model.py`
- Test: `backend/tests/test_match_model.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_match_model.py
from app.models.match_model import score_matrix, match_markets

def test_matrix_sums_to_one():
    M = score_matrix(1.6, 1.1, rho=-0.05, max_goals=10)
    total = sum(sum(row) for row in M)
    assert abs(total - 1.0) < 1e-6

def test_markets_1x2_sum_to_one():
    mk = match_markets(1.8, 1.0, rho=-0.05)
    p = mk["1x2"]
    assert abs(p["home"] + p["draw"] + p["away"] - 1.0) < 1e-6
    assert p["home"] > p["away"]  # higher home lambda

def test_over_under_complement():
    mk = match_markets(1.6, 1.2, rho=-0.05)
    assert abs(mk["totals"]["over_2.5"] + mk["totals"]["under_2.5"] - 1.0) < 1e-6

def test_btts_in_unit_interval():
    mk = match_markets(1.6, 1.2, rho=-0.05)
    assert 0 < mk["btts"]["yes"] < 1
    assert abs(mk["btts"]["yes"] + mk["btts"]["no"] - 1.0) < 1e-6
```

- [ ] **Step 2: Run test → FAIL**

Run: `cd backend && pytest tests/test_match_model.py -v`

- [ ] **Step 3: Write `backend/app/models/match_model.py`**

```python
"""Dixon-Coles score matrix and every market derived from it."""
from __future__ import annotations
from app.models.poisson import pmf
from app.models.ratings import _dc_tau


def score_matrix(lh: float, la: float, rho: float = -0.05, max_goals: int = 10) -> list[list[float]]:
    M = [[0.0] * (max_goals + 1) for _ in range(max_goals + 1)]
    s = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = pmf(i, lh) * pmf(j, la) * _dc_tau(i, j, lh, la, rho)
            p = max(p, 0.0)
            M[i][j] = p
            s += p
    if s > 0:
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                M[i][j] /= s
    return M


def match_markets(lh: float, la: float, rho: float = -0.05, max_goals: int = 10) -> dict:
    M = score_matrix(lh, la, rho, max_goals)
    home = draw = away = 0.0
    btts_yes = 0.0
    totals = {f"over_{l}": 0.0 for l in (0.5, 1.5, 2.5, 3.5, 4.5)}
    exact = {}
    exp_h = exp_a = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = M[i][j]
            if i > j: home += p
            elif i == j: draw += p
            else: away += p
            if i > 0 and j > 0: btts_yes += p
            exp_h += i * p; exp_a += j * p
            tot = i + j
            for line in (0.5, 1.5, 2.5, 3.5, 4.5):
                if tot > line:
                    totals[f"over_{line}"] += p
            if i <= 5 and j <= 5:
                exact[f"{i}-{j}"] = p
    top_scores = dict(sorted(exact.items(), key=lambda kv: kv[1], reverse=True)[:6])
    return {
        "1x2": {"home": home, "draw": draw, "away": away},
        "double_chance": {"home_draw": home + draw, "home_away": home + away,
                          "draw_away": draw + away},
        "dnb": {"home": home / (home + away) if (home + away) else 0.5,
                "away": away / (home + away) if (home + away) else 0.5},
        "totals": {**{k: v for k, v in totals.items()},
                   **{k.replace("over", "under"): 1 - v for k, v in totals.items()}},
        "btts": {"yes": btts_yes, "no": 1 - btts_yes},
        "exact_score": top_scores,
        "xg": {"home": exp_h, "away": exp_a, "total": exp_h + exp_a},
    }
```

- [ ] **Step 4: Run test → PASS**

Run: `cd backend && pytest tests/test_match_model.py -v`

- [ ] **Step 5: Commit**

```bash
cd backend && git add -A && git commit -m "feat: match score matrix + market derivation"
```

---

### Task 9: Player props (TDD)

**Files:**
- Create: `backend/app/models/player_props.py`
- Test: `backend/tests/test_player_props.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_player_props.py
from app.models.player_props import player_props, base_rates

def test_base_rates_by_line():
    assert base_rates("ST")["g"] > base_rates("CB")["g"]

def test_scorer_prob_increases_with_team_lambda():
    p_low = player_props("ST", tier=1.3, team_lambda=1.0)["scorer"]["model"]
    p_high = player_props("ST", tier=1.3, team_lambda=2.2)["scorer"]["model"]
    assert p_high > p_low
    assert 0 < p_low < 1

def test_gk_has_no_scorer_market():
    assert player_props("GK", tier=1.0, team_lambda=1.5)["scorer"] is None
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Write `backend/app/models/player_props.py`**

```python
"""Per-player Poisson props scaled by team attacking context."""
from __future__ import annotations
import math
from app.models.poisson import tail_ge

LINE = {"GK": "GK", "RB": "DEF", "CB": "DEF", "LB": "DEF", "RWB": "DEF", "LWB": "DEF",
        "CDM": "MID", "CM": "MID", "CAM": "MID", "DM": "MID", "RM": "MID", "LM": "MID"}
BASE = {
    "FWD": {"g": 0.52, "sh": 3.0, "sot": 1.25, "card": 0.15},
    "MID": {"g": 0.17, "sh": 1.7, "sot": 0.60, "card": 0.22},
    "DEF": {"g": 0.06, "sh": 0.7, "sot": 0.22, "card": 0.30},
    "GK":  {"g": 0.0,  "sh": 0.0, "sot": 0.0,  "card": 0.07},
}


def line_of(pos: str) -> str:
    return LINE.get(pos, "FWD")


def base_rates(pos: str) -> dict:
    return BASE[line_of(pos)]


def _choose_line(lam: float) -> float:
    return 0.5 if lam < 1 else round(lam) - 0.5


def player_props(pos: str, tier: float, team_lambda: float) -> dict:
    b = base_rates(pos)
    atk = team_lambda / 1.6
    gpg = b["g"] * tier * atk
    shg = b["sh"] * tier
    sotg = b["sot"] * tier
    scorer = None if line_of(pos) == "GK" else {"model": 1 - math.exp(-gpg)}
    def over(lam):
        L = _choose_line(lam)
        return {"line": L, "model": tail_ge(int(L + 0.5), lam)}
    return {
        "scorer": scorer,
        "shots": None if line_of(pos) == "GK" else over(shg),
        "sot": None if line_of(pos) == "GK" else over(sotg),
        "card": {"model": min(0.55, b["card"])},
    }
```

- [ ] **Step 4: Run → PASS**

- [ ] **Step 5: Commit** `feat: player props poisson model`

---

### Task 10: Tournament Monte-Carlo (TDD)

**Files:**
- Create: `backend/app/models/tournament.py`
- Test: `backend/tests/test_tournament.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_tournament.py
from app.models.tournament import simulate, GroupTeam

def _groups():
    # 12 groups of 4 with a clear seed ordering by strength
    groups = {}
    s = 90
    for L in "ABCDEFGHIJKL":
        groups[L] = [GroupTeam(code=f"{L}{k}", str_rating=s - k*8) for k in range(4)]
    return groups

def test_probabilities_sum_per_team_bounded():
    res = simulate(_groups(), sims=2000, seed=1)
    for code, p in res.team_probs.items():
        assert 0 <= p["win"] <= 1
        assert 0 <= p["qualify"] <= 1
        assert p["qualify"] >= p["win"]  # qualifying is easier than winning it all

def test_group_winner_probs_sum_to_one_per_group():
    res = simulate(_groups(), sims=2000, seed=1)
    for L in "ABCDEFGHIJKL":
        s = sum(res.group_winner[L].values())
        assert abs(s - 1.0) < 1e-9

def test_champion_probs_sum_to_one():
    res = simulate(_groups(), sims=2000, seed=1)
    assert abs(sum(res.champion.values()) - 1.0) < 1e-9
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Write `backend/app/models/tournament.py`**

```python
"""Monte-Carlo simulation of the WC2026 group + knockout structure."""
from __future__ import annotations
from dataclasses import dataclass, field
import math
import numpy as np


@dataclass
class GroupTeam:
    code: str
    str_rating: float


@dataclass
class SimResult:
    team_probs: dict[str, dict]
    group_winner: dict[str, dict]
    champion: dict[str, float]
    qualifiers_example: list[str] = field(default_factory=list)


def _pair_probs(sa: float, sb: float) -> tuple[float, float, float]:
    diff = sa - sb
    pa = 1 / (1 + 10 ** (-diff / 24))
    dr = min(0.30, max(0.09, 0.28 * math.exp(-abs(diff) / 46)))
    return (1 - dr) * pa, (1 - dr) * (1 - pa), dr


def simulate(groups: dict[str, list[GroupTeam]], sims: int = 50000, seed: int = 42) -> SimResult:
    rng = np.random.default_rng(seed)
    letters = list(groups.keys())
    all_codes = [t.code for g in groups.values() for t in g]
    strength = {t.code: t.str_rating for g in groups.values() for t in g}
    counts = {c: {"win": 0, "qualify": 0, "r16": 0, "qf": 0, "sf": 0, "final": 0, "champ": 0}
              for c in all_codes}
    gw_counts = {L: {t.code: 0 for t in groups[L]} for L in letters}

    for _ in range(sims):
        winners, runners, thirds = [], [], []
        for L in letters:
            g = groups[L]
            pts = {t.code: 0 for t in g}
            gd = {t.code: 0 for t in g}
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    a, b = g[i], g[j]
                    wa, wb, _ = _pair_probs(a.str_rating, b.str_rating)
                    r = rng.random()
                    if r < wa: pts[a.code] += 3; gd[a.code]+=1; gd[b.code]-=1
                    elif r < wa + wb: pts[b.code] += 3; gd[b.code]+=1; gd[a.code]-=1
                    else: pts[a.code]+=1; pts[b.code]+=1
            order = sorted(g, key=lambda t: (pts[t.code], gd[t.code], t.str_rating,
                                             rng.random()), reverse=True)
            gw_counts[L][order[0].code] += 1
            counts[order[0].code]["qualify"] += 1
            counts[order[1].code]["qualify"] += 1
            winners.append(order[0]); runners.append(order[1]); thirds.append(order[2])
        best_thirds = sorted(thirds, key=lambda t: t.str_rating, reverse=True)[:8]
        bracket = sorted(winners + runners + best_thirds,
                         key=lambda t: t.str_rating, reverse=True)
        # standard seeded bracket order over 32
        slots = [1, 2]
        while len(slots) < 32:
            length = len(slots) * 2; nxt = []
            for sidx in slots: nxt += [sidx, length + 1 - sidx]
            slots = nxt
        field32 = [bracket[s - 1] for s in slots]
        round_keys = ["r16", "qf", "sf", "final", "champ"]
        current = field32
        ridx = 0
        while len(current) > 1:
            nxt = []
            for k in range(0, len(current), 2):
                a, b = current[k], current[k + 1]
                wa, wb, _ = _pair_probs(a.str_rating, b.str_rating)
                tot = wa + wb or 1
                w = a if rng.random() < wa / tot else b
                nxt.append(w)
            for w in nxt:
                if ridx < len(round_keys):
                    counts[w.code][round_keys[ridx]] += 1
            current = nxt; ridx += 1
        champ = current[0]
        counts[champ.code]["champ"] += 1
        counts[champ.code]["win"] += 1

    team_probs = {c: {k: counts[c][k] / sims for k in counts[c]} for c in all_codes}
    group_winner = {L: {c: gw_counts[L][c] / sims for c in gw_counts[L]} for L in letters}
    champion = {c: team_probs[c]["champ"] for c in all_codes}
    return SimResult(team_probs=team_probs, group_winner=group_winner, champion=champion)
```

- [ ] **Step 4: Run → PASS** (champion sums to 1 because exactly one champ per sim; group winners likewise)

Run: `cd backend && pytest tests/test_tournament.py -v`

- [ ] **Step 5: Commit** `feat: monte-carlo tournament simulation`

---

## PHASE 3 — Providers, services, pricing

### Task 11: Provider interfaces + DTOs

**Files:**
- Create: `backend/app/providers/__init__.py`, `backend/app/providers/base.py`

- [ ] **Step 1: Create `backend/app/providers/base.py`**

```python
"""Provider protocols + transport DTOs (provider-agnostic)."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class OddsLine:
    market_key: str       # e.g. "h2h:m1"
    book: str
    selection: str        # "home"|"draw"|"away"|team code|"Over 2.5"...
    dec: float
    captured_at: datetime


@dataclass
class FixtureDTO:
    id: str
    home: str
    away: str
    group: str
    stage: str
    kickoff: datetime | None
    venue: str


@dataclass
class ResultDTO:
    home: str
    away: str
    home_goals: int
    away_goals: int
    days_ago: float
    competition: str = ""


@dataclass
class NewsItem:
    code: str
    tag: str       # injury|susp|lineup|form|intel
    text: str
    source: str
    url: str
    published_at: datetime


class OddsProvider(Protocol):
    def fetch_odds(self) -> list[OddsLine]: ...

class FootballProvider(Protocol):
    def fetch_fixtures(self) -> list[FixtureDTO]: ...
    def fetch_results(self) -> list[ResultDTO]: ...
    def fetch_squads(self) -> dict[str, list]: ...

class NewsProvider(Protocol):
    def fetch_news(self) -> list[NewsItem]: ...
```

- [ ] **Step 2: Commit** `feat: provider protocols and DTOs`

---

### Task 12: Seed providers (TDD)

**Files:**
- Create: `backend/app/providers/seed/__init__.py`, `seed_odds.py`, `seed_football.py`, `seed_news.py`
- Test: `backend/tests/test_seed_providers.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_seed_providers.py
from app.providers.seed.seed_football import SeedFootballProvider
from app.providers.seed.seed_odds import SeedOddsProvider
from app.providers.seed.seed_news import SeedNewsProvider

def test_seed_football_fixtures_and_results():
    p = SeedFootballProvider()
    assert len(p.fetch_fixtures()) >= 8
    assert len(p.fetch_results()) > 50
    assert "ESP" in p.fetch_squads()

def test_seed_odds_lines_present():
    lines = SeedOddsProvider().fetch_odds()
    assert any(l.market_key.startswith("h2h:") for l in lines)

def test_seed_news_has_tags():
    items = SeedNewsProvider().fetch_news()
    assert {i.tag for i in items} & {"form", "injury", "intel", "lineup", "susp"}
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Implement seed providers** building DTOs from `app.seed.seed_data` (fixtures from `MATCHES`, results from `synth_history()`, squads from `SQUADS`, odds from `MATCHES[*].odds` + `TEAMS[*].dec`, news a small static set transcribed from `project/match-extra.js` `WC.NEWS`).

```python
# seed_football.py
from datetime import datetime, timedelta, timezone
from app.providers.base import FixtureDTO, ResultDTO
from app.seed import seed_data

class SeedFootballProvider:
    def fetch_fixtures(self):
        out = []
        for m in seed_data.MATCHES:
            out.append(FixtureDTO(id=m["id"], home=m["home"], away=m["away"],
                                  group=m["group"], stage="group", kickoff=None,
                                  venue=m["venue"]))
        return out
    def fetch_results(self):
        now = datetime.now(timezone.utc)
        return [ResultDTO(home=h["home"], away=h["away"], home_goals=h["home_goals"],
                          away_goals=h["away_goals"], days_ago=h["days_ago"])
                for h in seed_data.synth_history()]
    def fetch_squads(self):
        return seed_data.SQUADS
```

```python
# seed_odds.py
from datetime import datetime, timezone
from app.providers.base import OddsLine
from app.seed import seed_data

class SeedOddsProvider:
    def fetch_odds(self):
        now = datetime.now(timezone.utc); out = []
        for m in seed_data.MATCHES:
            for sel, dec in zip(("home", "draw", "away"), m["odds"]):
                out.append(OddsLine(market_key=f"h2h:{m['id']}", book="seed",
                                    selection=sel, dec=dec, captured_at=now))
        for t in seed_data.TEAMS:
            out.append(OddsLine(market_key="outright", book="seed",
                                selection=t["code"], dec=t["dec"], captured_at=now))
        return out
```

```python
# seed_news.py — transcribe a subset of project/match-extra.js WC.NEWS
from datetime import datetime, timezone
from app.providers.base import NewsItem
NEWS = {"ESP": [("form", "Unbeaten in last 14 competitive matches."),
                ("lineup", "Pedri returns to full training.")]}  # extend per team
class SeedNewsProvider:
    def fetch_news(self):
        now = datetime.now(timezone.utc); out = []
        for code, items in NEWS.items():
            for tag, text in items:
                out.append(NewsItem(code=code, tag=tag, text=text, source="seed",
                                    url="", published_at=now))
        return out
```

- [ ] **Step 4: Run → PASS**

- [ ] **Step 5: Commit** `feat: seed providers (football, odds, news)`

---

### Task 13: Provider factory (env-based selection)

**Files:**
- Create: `backend/app/providers/factory.py`
- Test: `backend/tests/test_factory.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_factory.py
from app.providers.factory import get_football_provider, get_odds_provider, get_news_provider
from app.providers.seed.seed_football import SeedFootballProvider

def test_factory_falls_back_to_seed_without_keys(monkeypatch):
    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setenv("API_FOOTBALL_KEY", "")
    monkeypatch.setenv("ODDS_API_KEY", "")
    assert isinstance(get_football_provider(), SeedFootballProvider)
    assert get_odds_provider() is not None
    assert get_news_provider() is not None
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Implement `factory.py`**

```python
from app.config import get_settings
from app.providers.seed.seed_football import SeedFootballProvider
from app.providers.seed.seed_odds import SeedOddsProvider
from app.providers.seed.seed_news import SeedNewsProvider

def get_football_provider():
    s = get_settings()
    if s.has_football_key:
        from app.providers.api_football import ApiFootballAdapter
        return ApiFootballAdapter()
    return SeedFootballProvider()

def get_odds_provider():
    s = get_settings()
    if s.has_odds_key:
        from app.providers.the_odds_api import TheOddsApiAdapter
        return TheOddsApiAdapter()
    return SeedOddsProvider()

def get_news_provider():
    s = get_settings()
    if s.has_football_key:
        from app.providers.injuries import InjuriesNewsProvider
        return InjuriesNewsProvider()
    return SeedNewsProvider()
```

- [ ] **Step 4: Run → PASS**

- [ ] **Step 5: Commit** `feat: env-based provider factory with seed fallback`

---

### Task 14: Pricing + tournament services (TDD)

**Files:**
- Create: `backend/app/services/__init__.py`, `backend/app/services/pricing.py`, `backend/app/services/tournament_service.py`
- Test: `backend/tests/test_pricing.py`

`pricing.py` ties ratings → match_model → betting for each fixture and team, returning JSON-serializable snapshot payloads. `tournament_service.py` builds `GroupTeam` lists from team `str` ratings and runs `simulate`.

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_pricing.py
from app.services.pricing import price_match, price_outright
from app.models.ratings import fit_ratings
from app.seed import seed_data

def _ratings():
    codes = [t["code"] for t in seed_data.TEAMS]
    return fit_ratings(seed_data.synth_history(), codes)

def test_price_match_has_markets_and_ev():
    r = _ratings()
    snap = price_match("m1", "ESP", "CRO", r,
                       market_odds={"home": 1.62, "draw": 4.0, "away": 5.8})
    assert "1x2" in snap["markets"]
    assert "best" in snap and "ev" in snap["best"]

def test_price_outright_edge_signed():
    r = _ratings()
    rows = price_outright(r, {"ARG": 8.0, "NGA": 91.0})
    arg = next(x for x in rows if x["code"] == "ARG")
    assert "edge" in arg and "ev" in arg and "kelly" in arg
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Implement `pricing.py`**

```python
"""Orchestrates ratings -> match model -> betting into snapshot payloads."""
from __future__ import annotations
from app.models.match_model import match_markets
from app.models import betting as B


def price_match(match_id, home, away, ratings, market_odds: dict) -> dict:
    lh, la = ratings.lambdas(home, away)
    mk = match_markets(lh, la, rho=ratings.rho)
    p = mk["1x2"]
    fair = B.fair_probs([market_odds["home"], market_odds["draw"], market_odds["away"]])
    legs = []
    for kind, fairp in zip(("home", "draw", "away"), fair):
        dec = market_odds[kind]; model = p[kind]
        legs.append({"kind": kind, "dec": dec, "model": model,
                     "implied": B.implied_prob(dec), "fair": fairp,
                     "edge": model - fairp, "ev": B.ev(model, dec),
                     "kelly": B.kelly_full(model, dec),
                     "verdict": B.verdict(model - fairp)})
    best = max(legs, key=lambda x: x["ev"])
    return {"id": match_id, "home": home, "away": away, "markets": mk,
            "legs": legs, "best": best,
            "xg": mk["xg"], "conf": B.confidence(max(p.values()))}


def price_outright(ratings, dec_by_code: dict) -> list[dict]:
    # model outright prob ∝ exp(net rating); de-vig the book outright column for "fair"
    import math
    nets = {c: ratings.teams[c].attack - ratings.teams[c].defense for c in dec_by_code}
    z = {c: math.exp(2.2 * nets[c]) for c in nets}
    s = sum(z.values())
    model = {c: z[c] / s for c in z}
    codes = list(dec_by_code)
    fair = B.fair_probs([dec_by_code[c] for c in codes])
    fair_by = dict(zip(codes, fair))
    rows = []
    for c in codes:
        dec = dec_by_code[c]; m = model[c]
        rows.append({"code": c, "dec": dec, "model": m, "implied": B.implied_prob(dec),
                     "fair": fair_by[c], "edge": m - fair_by[c], "ev": B.ev(m, dec),
                     "kelly": B.kelly_full(m, dec), "verdict": B.verdict(m - fair_by[c]),
                     "str": ratings.teams[c].str_rating})
    return rows
```

```python
# tournament_service.py
from app.models.tournament import simulate, GroupTeam

def run_tournament(ratings, group_of: dict[str, str], sims: int = 50000):
    groups: dict[str, list[GroupTeam]] = {}
    for code, L in group_of.items():
        groups.setdefault(L, []).append(GroupTeam(code=code,
            str_rating=ratings.teams[code].str_rating))
    return simulate(groups, sims=sims)
```

- [ ] **Step 4: Run → PASS**

- [ ] **Step 5: Commit** `feat: pricing + tournament services`

---

### Task 15: Ingestion + refresh pipeline (writes snapshots to DB)

**Files:**
- Create: `backend/app/services/ingestion.py`, `backend/app/services/news.py`, `backend/app/cli.py`
- Test: `backend/tests/test_refresh.py`

`ingestion.run_refresh(db)` = fetch via factory providers → upsert teams/players/matches/results/odds → fit ratings → price all matches + outright → simulate tournament → write `model_snapshots`, `tournament_snapshot`, `team_news`.

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_refresh.py
from app.services.ingestion import run_refresh
from app.db.models import ModelSnapshot, TournamentSnapshot, Team

def test_refresh_populates_snapshots(db_session):
    run_refresh(db_session, sims=500)
    assert db_session.query(Team).count() == 48
    assert db_session.query(ModelSnapshot).filter_by(kind="match").count() >= 8
    assert db_session.query(ModelSnapshot).filter_by(kind="outright").count() >= 1
    assert db_session.query(TournamentSnapshot).count() == 1
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Implement `ingestion.run_refresh`** using the factory + seed_data group map + services, persisting JSON payloads. (Full code: upsert teams from `seed_data.TEAMS`, fit ratings on fetched results, loop matches calling `price_match` with odds grouped by `market_key`, call `price_outright`, `run_tournament`, write rows with `created_at=datetime.utcnow()`.)

- [ ] **Step 4: Run → PASS** (uses sqlite fixture; sims=500 keeps it fast)

- [ ] **Step 5: Commit** `feat: ingestion + refresh pipeline`

- [ ] **Step 6: Add `cli.py`** with `refresh` (real DB) and `init-db` (create_all) commands; commit `feat: cli refresh/init-db`.

---

## PHASE 4 — API (deadline-critical "tested" milestone)

### Task 16: Pydantic schemas

**Files:** Create `backend/app/schemas/*.py` mirroring frontend shape (outright row, match with markets/legs, group rows, bracket rounds, team detail, player, bankroll, news, meta). Each is a `pydantic.BaseModel`. Commit `feat: response schemas`.

### Task 17: Read endpoints over snapshots (TDD)

**Files:**
- Create: `backend/app/main.py`, `backend/app/api/deps.py`, `routes_outright.py`, `routes_matches.py`, `routes_groups.py`, `routes_bracket.py`, `routes_teams.py`, `routes_players.py`, `routes_news.py`, `routes_meta.py`, `routes_admin.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_api.py
from app.services.ingestion import run_refresh

def test_full_api_flow(client, db_session):
    run_refresh(db_session, sims=400)
    assert client.get("/meta").status_code == 200
    r = client.get("/outright"); assert r.status_code == 200 and len(r.json()) == 48
    assert client.get("/matches").json()
    mid = client.get("/matches").json()[0]["id"]
    assert client.get(f"/matches/{mid}").json()["markets"]
    assert client.get("/groups").json()
    assert client.get("/bracket").json()["champion"]
    assert client.get("/news/ESP").status_code == 200
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Implement `main.py`** (create app, add CORS for `http://localhost:*`, include routers) and each router reading the latest snapshots from DB and shaping to schemas. `/admin/refresh` calls `run_refresh`.

- [ ] **Step 4: Run → PASS**

- [ ] **Step 5: Commit** `feat: read API endpoints over snapshots`

---

### Task 18: Bankroll & bets (real-time, TDD)

**Files:**
- Create: `backend/app/services/bankroll.py`, `backend/app/api/routes_bankroll.py`
- Test: `backend/tests/test_bankroll.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_bankroll.py
def test_place_settle_bankroll(client, db_session):
    body = {"key": "m:m1:home", "pick": "Spain ML", "team": "ESP",
            "market": "Match Result", "stake": 40, "dec": 1.62}
    r = client.post("/bankroll/bets", json=body); assert r.status_code == 201
    bet_id = r.json()["id"]
    bk = client.get("/bankroll").json()
    assert any(b["id"] == bet_id for b in bk["open_bets"])
    r2 = client.post(f"/bankroll/bets/{bet_id}/settle", json={"result": "won"})
    assert r2.status_code == 200
    bk2 = client.get("/bankroll").json()
    assert bk2["balance"] != bk["balance"]

def test_delete_open_bet(client, db_session):
    body = {"key": "x", "pick": "p", "stake": 10, "dec": 2.0}
    bid = client.post("/bankroll/bets", json=body).json()["id"]
    assert client.delete(f"/bankroll/bets/{bid}").status_code == 204
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Implement** `bankroll.py` (place_bet, settle_bet with pnl = stake*(dec-1) on win / -stake on loss / 0 on void, delete_open, get_state with starting bankroll 1000 + ledger) and the router. Balance = 1000 + sum(settled pnl).

- [ ] **Step 4: Run → PASS**

- [ ] **Step 5: Commit** `feat: bankroll + bets endpoints`

---

## PHASE 5 — Real adapters (env-gated, validated vs seed contract)

### Task 19: The Odds API adapter

**Files:** Create `backend/app/providers/the_odds_api.py` + `backend/tests/test_the_odds_api.py` (mock httpx with a recorded JSON fixture; assert it maps to `OddsLine` the same shape seed produces). Implement GET `/v4/sports/soccer_fifa_world_cup/odds?regions=eu&markets=h2h,totals&oddsFormat=decimal` with `apiKey`. Map bookmakers→`OddsLine`. Respect rate-limit via `provider_calls`. Commit `feat: The Odds API adapter`.

### Task 20: API-Football adapter + injuries news

**Files:** Create `backend/app/providers/api_football.py`, `backend/app/providers/injuries.py`, `backend/app/providers/rss_news.py` + tests with mocked httpx/feedparser fixtures.
- `api_football.py`: fixtures (`/fixtures?league=1&season=2026`), results (`/fixtures` finished), squads (`/players/squads`), headers `x-apisports-key`.
- `injuries.py`: `/injuries` → `NewsItem(tag="injury"/"susp")`.
- `rss_news.py`: parse BBC/ESPN/Sky/CBS RSS via `feedparser`, filter by team name → `NewsItem(tag="form"/"intel")`.
Commit `feat: API-Football + injuries + RSS adapters`.

### Task 21: README + .env wiring + manual smoke

**Files:** Create `backend/README.md` (Postgres via docker one-liner, `alembic upgrade head`, `python -m app.cli refresh`, `uvicorn app.main:app --reload`, how to add keys). Add `docker-compose.yml` for Postgres. Manual smoke: run server on seed, hit each endpoint. Commit `docs: backend readme + compose + env`.

---

## Self-Review notes (addressed)

- **Spec coverage:** ratings/Dixon-Coles (T7), match markets (T8), player props (T9), Monte-Carlo (T10), de-vig/Kelly/verdict (T3), providers + seed fallback (T11–13), real adapters (T19–20), persistence/snapshots (T4,T15), API incl. news (T16–18), bankroll (T18), tests throughout, news layer injuries+RSS (T12,T20). All spec sections map to tasks.
- **Type consistency:** `RatingsModel.lambdas/rho` used by `match_model` and `pricing`; `GroupTeam`/`SimResult` consistent T10↔T14; `OddsLine/FixtureDTO/ResultDTO/NewsItem` consistent across seed + real adapters; `_dc_tau` defined in `ratings.py` and reused by `match_model.py`.
- **No placeholders:** algo-critical code given in full; routine routers/schemas specified with exact endpoints, fields, and tests that pin their behavior.
- **Deadline:** Phases 1–4 deliver a fully tested app on seed (no keys) — the "tested & approved" milestone; Phase 5 layers real data, gated only by keys.
