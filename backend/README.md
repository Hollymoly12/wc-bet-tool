# WC Bet Tool — Backend

FastAPI algorithmic engine for the 2026 FIFA World Cup betting tool.

Runs fully on seed data with no API keys. Add real provider keys to `backend/.env` to pull live odds and fixtures.

---

## Overview

The backend exposes a REST API that the React front-end (`project/`) consumes. It pre-computes betting snapshots (odds, EV, Kelly stake, verdicts) via a **market-anchored Dixon-Coles + Monte-Carlo** model, persists them to a database, and serves them fast. Bets and bankroll are real-time. A CLI/cron job (`python -m app.cli refresh`) re-runs the pipeline on demand.

---

## Architecture

```
Providers                        Algo core (pure, testable)       API (FastAPI)
├─ TheOddsApiAdapter             ├─ ratings.py                    GET /outright
│   (ODDS_API_KEY)               │   Dixon-Coles MLE (attack/     GET /matches[/{id}]
├─ SeedOddsProvider              │   defense/home-adv/rho) + Elo  GET /groups
│                                ├─ match_model.py                GET /bracket
├─ ApiFootballAdapter            │   score matrix → 1X2, O/U,     GET /teams[/{code}]
│   (API_FOOTBALL_KEY)           │   BTTS, DNB, exact score, xG   GET /players[/{id}]
├─ SeedFootballProvider          ├─ tournament.py                 GET /news/{code}
│                                │   Monte-Carlo 12 groups + KO   GET /bankroll
├─ InjuriesAdapter + RssNews     ├─ player_props.py (Poisson)     POST /bankroll/bets
└─ SeedNewsProvider              └─ betting.py                    POST /admin/refresh
                                     devig, EV, Kelly, verdict    ...
                    Services: ingestion → pricing → tournament_service → snapshots
```

### Market-anchored strength (why it matters)

A pure Dixon-Coles fit on the available data gave degenerate results — e.g. Saudi Arabia 27% to win the tournament — because API-Football's free tier only covers seasons 2022–2024 and results are confederation-siloed (European teams have far more calibration matches than Asian or CONCACAF sides).

The fix is `app/services/market_anchor.py`: de-vig the outright-winner market odds to produce fair champion probabilities, convert to a z-scored log-strength, then **blend that market anchor with the Dixon-Coles model rating at up to 35% weight** (weighted by calibration match count). Teams with few real results are almost entirely market-anchored; data-rich teams allow a small model nudge. Output: Spain/France/England/Brazil at the top, validated against real outright markets.

---

## Quickstart (local)

### 1. Create the virtual environment

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows
```

### 2. Install dependencies

```bash
pip install -e '.[dev]'
```

### 3. Configure environment

```bash
cp .env.example .env
# Leave keys blank for seed (offline) mode — see "Activating real data" below
```

The default `DATABASE_URL` in `.env.example` points at Postgres. For local development, override it to use SQLite — no Docker needed:

```bash
# In .env
DATABASE_URL=sqlite:///./wcbet.db
```

The app is fully DB-agnostic via SQLAlchemy. SQLite is the local default; Supabase Postgres is used in production.

### 4. Initialise the database

Either approach works:

```bash
# Option A — quick (no Alembic, just creates all tables)
python -m app.cli init-db

# Option B — Alembic migrations (use this for production-like setup)
alembic upgrade head
```

### 5. Load data and start the server

```bash
# Seed (or real) data refresh — run this once to populate snapshots
python -m app.cli refresh

# Development server
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`.

### 6. Smoke test

```bash
# Hits every endpoint via TestClient + in-memory SQLite — no running server needed
python scripts/smoke.py
```

### 7. Provider diagnostics

```bash
# Calls each real provider once and reports name resolution; read-only, no DB writes
python scripts/diagnose_providers.py
```

---

## Running tests

```bash
pytest tests/ -q        # 192 tests, ~48s, hermetic (no network or keys)
ruff check app tests    # lint
```

Tests use in-memory SQLite and seed providers — no API keys and no running database instance required.

---

## Activating real data

Set keys in `backend/.env`:

```dotenv
# The Odds API — https://the-odds-api.com
ODDS_API_KEY=your_key_here

# API-Football — https://www.api-football.com
API_FOOTBALL_KEY=your_key_here
```

When a key is present the corresponding real adapter is selected automatically; missing keys fall back to seed transparently.

After updating `.env`, trigger a refresh to pull live data:

```bash
python -m app.cli refresh
```

### Quota notes

| Provider | Free-tier limit | Notes |
|---|---|---|
| API-Football | 100 req/day, ~10/min | Seasons 2022–2024 only (season 2026 blocked on free tier). Calibration uses WC2022, Nations League, Euro, Copa, AFCON, qualifiers. Squads/lineups remain seed-data. |
| The Odds API | 500 credits/month | 48 real teams + 12 groups derived by clustering the 72 h2h events (no external draw source). |

Run `python -m app.cli refresh` only a few times per day to stay within the 100 req/day API-Football quota.

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/outright` | 48 teams: model prob, implied, edge, EV, Kelly, confidence, form, str |
| `GET` | `/matches` | All fixtures with full market pricing + xG |
| `GET` | `/matches/{id}` | Single fixture with markets, xG, and H2H |
| `GET` | `/groups` | 12 groups: standings sim, group-winner and qualify markets |
| `GET` | `/bracket` | Projected R32→Final + champion |
| `GET` | `/teams` | All 48 teams: code, name, group, str, form, elo |
| `GET` | `/teams/{code}` | Team detail: squad, outright row, news |
| `GET` | `/players` | Player list for a team (`?code=ESP`) |
| `GET` | `/players/{id}` | Player detail + Poisson props (scorer, shots, cards) |
| `GET` | `/news/{code}` | Team news items (injuries + RSS) |
| `GET` | `/bankroll` | Current balance, open bets, settled bets |
| `POST` | `/bankroll/bets` | Place a bet |
| `DELETE` | `/bankroll/bets/{id}` | Remove an open bet |
| `POST` | `/bankroll/bets/{id}/settle` | Settle a bet (`{"result": "won"|"lost"|"void"}`) |
| `GET` | `/meta` | Risk profiles, supported odds formats |
| `POST` | `/admin/refresh` | Trigger full ingestion + model recompute (async-safe via snapshots) |

---

## Notes and known limitations

- **Squads and lineups are seed data** on the API-Football free plan. The free tier does not expose season-2026 player or lineup endpoints. Player props (scorer probability, shots, cards) are computed from seed squad data and will not reflect real tournament selections until upgraded API access is available.
- **The local default is SQLite** (`DATABASE_URL=sqlite:///./wcbet.db`). The old README incorrectly said Postgres was required; Docker is not needed for local development. Production uses Supabase Postgres — see the root `README.md` for the deploy guide.
- **Groups are derived, not from a draw API.** The 12 WC2026 groups are inferred by clustering the 72 head-to-head match events returned by The Odds API. No separate draw endpoint is consumed.
- Interactive API docs: `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.
