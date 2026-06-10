# WC Bet Tool — 2026 FIFA World Cup Betting Engine

An edge-finding betting decision-support tool for WC2026: a market-anchored statistical model (Dixon-Coles + Monte-Carlo) served over FastAPI, with a React prototype front-end and a planned Vercel deployment.

Spec: [`docs/superpowers/specs/2026-06-09-wc-bet-tool-backend-design.md`](docs/superpowers/specs/2026-06-09-wc-bet-tool-backend-design.md)
Plan: [`docs/superpowers/plans/2026-06-09-wc-bet-tool-backend.md`](docs/superpowers/plans/2026-06-09-wc-bet-tool-backend.md)

---

## What this is

The tool compares a model-derived probability against de-vigged market odds to surface positive-EV bets. It covers:

- **Outright winner** market (48 teams, champion/qualify/stage probabilities from 50 000 Monte-Carlo simulations)
- **Match markets** (1X2, O/U, BTTS, DNB, Double Chance, correct score, xG)
- **Player props** (scorer, shots, cards via Poisson)
- **Bankroll management** (Kelly staking with risk-profile caps, bet ledger, P&L)

The model anchors team strength to outright market odds (de-vigged champion probability z-score) to prevent confederation-siloed noise from the free-tier football data from producing garbage predictions. A Dixon-Coles model nudges ratings by up to 35% where calibration data is rich.

---

## Repo layout

```
backend/          FastAPI app, algo core, DB layer, CLI, tests
  app/
    models/       Pure algo modules (poisson, ratings, match_model, tournament, betting)
    services/     Ingestion, pricing, market_anchor, bankroll, news
    providers/    Real adapters (TheOddsApi, ApiFootball) + seed fallbacks
    api/          FastAPI route handlers
    db/           SQLAlchemy ORM + session
  tests/          192 hermetic tests (~48s, no network, no keys)
  scripts/        smoke.py, diagnose_providers.py

project/          React front-end prototype (client-side data, being replaced by the API)

frontend/         Vercel-deployed front-end (being added)

docs/
  superpowers/
    specs/        Design documents
    plans/        Implementation plans

.github/
  workflows/      refresh.yml — cron job that runs the algo 4x/day
```

See [`backend/README.md`](backend/README.md) for the full local-dev quickstart.

---

## Deploy guide

The intended production setup is: **GitHub Actions cron** refreshes data and writes to **Supabase Postgres** four times a day — independent of any local machine being on — and **Vercel** hosts the front-end and a slim read API.

### 1. GitHub — push and configure secrets

Push this repo to GitHub, then add three **Actions secrets** (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `DATABASE_URL` | Supabase Postgres connection string (see step 2) |
| `ODDS_API_KEY` | From https://the-odds-api.com |
| `API_FOOTBALL_KEY` | From https://www.api-football.com |

The workflow at `.github/workflows/refresh.yml` runs `python -m app.cli refresh` on a cron schedule (4x/day). It uses these secrets so the model updates automatically even when your machine is off.

### 2. Supabase — managed Postgres

1. Create a free project at https://supabase.com.
2. Go to **Project Settings → Database → Connection string** and copy the URI.
3. Format it for psycopg3 (the driver used by this app):

```
postgresql+psycopg://postgres:[YOUR-PASSWORD]@[HOST]:5432/postgres
```

4. Set this string as `DATABASE_URL` in both the GitHub secret (step 1) and the Vercel environment variable (step 3).
5. Run migrations once to create the schema. You can do this locally pointing at the Supabase URL, or let the first cron run do it:

```bash
# From backend/
DATABASE_URL=postgresql+psycopg://... alembic upgrade head
```

> **Supabase free tier note:** Free projects pause after 7 days of inactivity. The daily refresh cron keeps the project warm automatically. If you stop the cron, resume the project manually in the Supabase dashboard before restarting.

### 3. Vercel — front-end and read API

1. Import the repo into Vercel.
2. Set the **root directory** to `frontend/` for the front-end deployment.
3. Add environment variables in the Vercel project settings:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Same Supabase connection string (read-only use — Vercel only serves snapshots) |
| `VITE_API_URL` | The Vercel deployment URL of the backend (or a separate Railway/Fly deployment) |

4. The backend can be deployed as a Vercel serverless function via a `vercel.json` in `backend/` (WSGI adapter for FastAPI). Alternatively, deploy the backend separately on Railway or Fly.io and point `VITE_API_URL` at it.

---

## Free-tier quota warnings

| Provider | Limit | Risk |
|---|---|---|
| API-Football | 100 req/day, ~10/min | 4 cron runs/day = ~24 requests/run — well within limit. Do not trigger manual refreshes repeatedly. Season 2026 fixtures are blocked on the free plan; calibration uses 2022–2024 data only. |
| The Odds API | 500 credits/month | Each `/odds` fetch costs ~1–4 credits depending on markets. 4 runs/day x 30 days = 120 fetches minimum — monitor usage at the dashboard. |
| Supabase | 500 MB storage, 2 CPU-sec/req | Snapshot rows are small JSON blobs; well within free limits for a single-user tool. |

---

## Local development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
# Set DATABASE_URL=sqlite:///./wcbet.db in .env for local SQLite (no Docker needed)
python -m app.cli init-db
python -m app.cli refresh
uvicorn app.main:app --reload
```

Full details: [`backend/README.md`](backend/README.md)
