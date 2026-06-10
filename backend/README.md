# WC Bet Tool — Back-end

FastAPI + PostgreSQL betting model for the 2026 FIFA World Cup.

Runs fully on seed data with no API keys. Add real provider keys to `.env` to
switch to live odds and fixtures.

---

## Prerequisites

- Python 3.11+
- Docker (for the Postgres container)

---

## Quick start

### 1. Create and activate the virtual environment

```bash
python -m venv .venv
source .venv/bin/activate           # macOS / Linux
.venv\Scripts\activate              # Windows
```

### 2. Install dependencies (including dev extras)

```bash
.venv/bin/pip install -e '.[dev]'
```

### 3. Start Postgres

```bash
docker compose up -d
```

This starts a `postgres:16` container on port 5432 (user: `wc`, password: `wc`,
database: `wcbet`).

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env if you want to use real data providers (see "Real data" below)
```

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Seed the database and start the server

Load seed data (no keys required):

```bash
python -m app.cli refresh
```

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API is now available at `http://localhost:8000`.

---

## Running tests

```bash
.venv/bin/pytest tests/ -q
```

All 78+ tests should pass without any API keys or a running Postgres instance
(tests use an in-memory SQLite database).

---

## Activating real data providers

Set the relevant keys in `.env`:

```dotenv
# The Odds API  — https://the-odds-api.com
ODDS_API_KEY=your_odds_api_key_here

# API-Football  — https://www.api-football.com
API_FOOTBALL_KEY=your_api_football_key_here
```

When either key is present the corresponding adapter is used automatically.
Without keys the app falls back to seed data transparently.

After updating `.env` run another refresh to pull live data:

```bash
python -m app.cli refresh
```

---

## Architecture summary

```
providers/
  seed/           SeedFootballProvider, SeedOddsProvider, SeedNewsProvider
  the_odds_api.py TheOddsApiAdapter     (used when ODDS_API_KEY set)
  api_football.py ApiFootballAdapter    (used when API_FOOTBALL_KEY set)
  injuries.py     InjuriesNewsProvider  (used when API_FOOTBALL_KEY set)
  rss_news.py     RssNewsAdapter        (always available)
  teamnames.py    to_code() + fixture_id() shared name-resolution helpers
  factory.py      selects real adapter or seed fallback from env
```

Both `TheOddsApiAdapter` and `ApiFootballAdapter` derive fixture IDs as
`{HOME_CODE}_{AWAY_CODE}` via `teamnames.fixture_id()`, so odds and fixtures
join by construction during ingestion.

---

## docker-compose services

| Service  | Image       | Port | Credentials         |
|----------|-------------|------|---------------------|
| postgres | postgres:16 | 5432 | wc / wc / wcbet     |
