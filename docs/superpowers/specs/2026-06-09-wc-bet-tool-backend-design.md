# WC Bet Tool — Back-end & Algorithmic Engine — Design

**Date:** 2026-06-09
**Author:** Tom (with Claude)
**Status:** Approved (design) — pending spec review
**Deadline:** Tested & approved by Friday 2026-06-12

## 1. Purpose & Context

`EDGE / WC Bet Tool` is a betting decision-support tool for the 2026 FIFA World Cup.
A React front-end prototype already exists (`project/`). Today **all** betting math and
data are hard-coded client-side in `data.js`, `match-extra.js`, `tournament.js`,
`lineups.js`, `squads*.js` and exposed via a global `window.WC`.

This project builds the **real back-end and algorithmic engine** that replaces those
client-side mocks with:

- A real **independent statistical model** (team ratings → Dixon-Coles match model →
  Monte-Carlo tournament simulation), compared against the market to surface value.
- **Real data integration** (The Odds API for odds, API-Football for fixtures /
  results / squads / lineups / injuries), with a **Seed fallback** so the whole app
  runs and is fully testable with **no API keys**.
- A **FastAPI** service backed by **PostgreSQL** (single user, no auth) serving data in
  the shape the front-end already consumes.

### Scope boundaries (YAGNI)

- **In:** back-end API, statistical models, data providers (+ seed fallback), bankroll/
  bets persistence, team-news layer (injuries + RSS), tests, migrations.
- **Out (v1):** rebuilding the React front-end (it stays as-is; the API matches its data
  shape), multi-user/auth, payment, live in-play streaming, mobile apps.

## 2. Key Decisions (locked)

| Topic | Decision |
|---|---|
| Data source | Real APIs: **The Odds API** (odds) + **API-Football** (fixtures, results, squads, lineups, injuries) |
| API keys | **None yet** → real adapters built, **Seed fallback** auto-engages when keys absent |
| Stack | **Python 3.11+ / FastAPI** |
| Persistence | **PostgreSQL** via SQLAlchemy + Alembic, **single user, no auth** |
| Model | **Independent statistical model**: ratings + Dixon-Coles + Monte-Carlo |
| Compute timing | **Approach B — pre-computed snapshots**: heavy model runs in a service, persists snapshots; API serves snapshots fast. Bets/bankroll are real-time. |
| Lineups/squads | API-Football (`/players/squads`, `/fixtures/lineups`) |
| Team news | Pluggable `NewsProvider`: API-Football `/injuries` (structured) + **RSS aggregation** (BBC/ESPN/Sky/CBS), per-team filtered. Optional scraper adapter slot (not a v1 dependency). |

## 3. Architecture

```
Providers (interfaces)            Algo core (pure, testable)        API (FastAPI)
├─ OddsProvider                   ├─ ratings.py                     ├─ /outright
│  ├─ TheOddsApiAdapter           │   Dixon-Coles MLE (attack/       ├─ /matches, /matches/{id}
│  └─ SeedOddsProvider            │   defense/home-adv/rho) + Elo    ├─ /groups
├─ FootballProvider               ├─ match_model.py                 ├─ /bracket
│  ├─ ApiFootballAdapter          │   score matrix → 1X2, O/U,       ├─ /teams, /teams/{code}
│  └─ SeedFootballProvider        │   BTTS, DC, DNB, exact score, xG ├─ /players, /players/{id}
├─ NewsProvider                   ├─ tournament.py                  ├─ /news/{code}
│  ├─ InjuriesAdapter (API-Foot)  │   Monte-Carlo groups 12×4 + KO   ├─ /bankroll/* (bets CRUD)
│  ├─ RssNewsAdapter              │   → outright/qualify/stage probs ├─ /meta
│  └─ SeedNewsProvider            ├─ player_props.py (Poisson)       └─ /admin/refresh
└─ cache.py (DB cache + rate-lim) └─ betting.py (devig Shin/mult,
                                      EV, Kelly+risk+cap, verdict)
Services: ingestion.py · pricing.py (orchestration) · bankroll.py · news.py
```

Each algo module is **pure**: inputs are numbers/ratings/probabilities, outputs are
probabilities/odds. No DB or network access inside the model code → unit-testable in
isolation. Services wire providers + DB + models together.

## 4. Algorithmic Core (detail)

### 4.1 `ratings.py` — team strength
- Fit a **Dixon-Coles** model by maximum likelihood on historical match results
  (from API-Football, or seed history): per-team **attack** & **defense** parameters,
  global **home advantage**, and the **rho** low-score dependency correction.
- **Time decay**: recent matches weighted higher (exponential half-life ~ 18 months).
- **Elo** maintained as a secondary/robust rating, used to (a) prior/shrink teams with
  few observed matches, (b) seed strength for the `str` 0–100 power rating the front-end
  uses, (c) sanity fallback.
- Output: `TeamRatings { attack, defense, elo, str }` per team + `home_adv`, `rho`.

### 4.2 `match_model.py` — single fixture
- From two teams' ratings → expected goals `lambda_home`, `lambda_away` (incl. home adv).
- Build a **score matrix** P(i,j) for i,j ∈ 0..MAXG (8) using independent Poisson with the
  **Dixon-Coles tau** correction for (0,0),(0,1),(1,0),(1,1).
- Derive **every market** from the matrix: 1X2, Double Chance, Draw No Bet,
  Over/Under {0.5,1.5,2.5,3.5,4.5}, BTTS yes/no, correct score top-N, expected goals.
- Output: `MatchProbs` dict consumed by pricing + player props (for team λ context).

### 4.3 `tournament.py` — Monte-Carlo simulation
- N ≈ 50 000 simulations. Each sim:
  1. Simulate all group matches via `match_model` (sample a scoreline from the matrix).
  2. Apply **WC 2026 rules**: 12 groups of 4, **top 2 + 8 best third-placed** → Round of 32.
  3. Tie-breakers: points → goal difference → goals → (seeded random).
  4. Build the bracket and simulate knockout (KO: draw → extra time/penalties handled as a
     coin-leaning-to-favorite from match probs).
- Accumulate per team: **group-winner**, **qualify (top-2)**, **best-third**, **reach R16/
  QF/SF/Final**, **win tournament**. Plus per-group standings distribution (expected points,
  rank probabilities) and projected most-likely bracket.
- Deterministic via a seeded RNG (stable across runs / snapshots).

### 4.4 `player_props.py`
- Per-player base rates by position (goals, shots, SOT, cards) scaled by player tier and
  the team's match λ context → **anytime scorer**, **over X shots/SOT**, **to be carded**
  probabilities via Poisson tails.

### 4.5 `betting.py` — value & staking
- **De-vig** market odds to fair probabilities: **Shin** method (primary) + **multiplicative**
  (fallback), across multiple books → consensus fair line.
- **Edge** = p_model − p_fair; **EV** = p_model · dec − 1.
- **Kelly** fraction (full), then apply **risk profile** multiplier + cap:
  conservative 0.25×/cap 4%, balanced 0.5×/cap 7%, aggressive 1.0×/cap 12% (from prototype).
- **Recommended stake** = bankroll · min(kelly·mult, cap), rounded to 5.
- **Verdict**: Strong / Value / Pass / Avoid from EV thresholds; **confidence** from model
  variance + data coverage.

All formulas covered by unit tests against known values (Poisson, de-vig, Kelly, EV).

## 5. Data & Persistence (PostgreSQL)

SQLAlchemy ORM + Alembic migrations. Core tables:

- `teams` — code, name, group, colors, elo/attack/defense, str, form.
- `players` — team, number, name, position, club, tier, rates.
- `matches` — fixtures (group + KO), home/away, datetime, venue, stage.
- `match_results` — historical results for calibration (date, teams, score, competition, weight).
- `odds_snapshots` — raw odds per book + market + timestamp.
- `model_snapshots` — computed model probabilities/odds/EV per selection (served to API).
- `tournament_snapshot` — outright/qualify/stage probabilities + projected bracket (one current).
- `team_news` — code, tag, text, source, url, timestamp.
- `bets` — selection, market, stake, odds, status (open/won/lost/void), placed_at.
- `bankroll_transactions` — ledger (deposit, bet, settle) → balance derived.
- `provider_calls` — provider, endpoint, ts (rate-limit accounting).

## 6. Providers & key-less mode

- `OddsProvider`, `FootballProvider`, `NewsProvider` are **Protocols/ABCs**.
- Real adapters: `TheOddsApiAdapter`, `ApiFootballAdapter`, `InjuriesAdapter` (API-Football),
  `RssNewsAdapter` (feedparser over BBC/ESPN/Sky/CBS).
- **Seed adapters** derive from the existing prototype data (ported to Python fixtures):
  48 teams, 8+ marquee matches, squads, history → the model can fully calibrate & simulate.
- **Selection by env**: a `provider_factory` reads `ODDS_API_KEY`, `API_FOOTBALL_KEY`. If a
  key is missing → that domain falls back to its Seed adapter automatically and logs it.
- `cache.py`: DB-backed cache with TTL + simple rate-limit guard via `provider_calls`.

## 7. API (FastAPI)

Pydantic response schemas mirror the front-end's expected data shape (`teams`, `matches`
with `markets`, `groups`, `bracket`, `players`, `bankroll`, `news`). CORS enabled for the
local front-end.

- `GET /outright` — 48 teams with model prob, implied, edge, EV, kelly, conf, form, str.
- `GET /matches`, `GET /matches/{id}` — fixtures + full markets + xG + H2H.
- `GET /groups` — 12 groups: standings sim, group-winner & qualify markets.
- `GET /bracket` — projected R32→Final + champion.
- `GET /teams`, `GET /teams/{code}` — team stats + squad/lineup.
- `GET /players`, `GET /players/{id}` — player stats + props.
- `GET /news/{code}` — team news (injuries + RSS).
- `POST /bankroll/bets`, `GET /bankroll`, `DELETE /bankroll/bets/{id}`,
  `POST /bankroll/bets/{id}/settle` — real-time bet/bankroll management.
- `GET /meta` — risk profiles, odds formats.
- `POST /admin/refresh` — trigger ingestion + recompute snapshots (also runnable as CLI/cron).

## 8. Refresh / pricing pipeline (Approach B)

`POST /admin/refresh` (or `python -m app.cli refresh`):
1. **Ingest**: fetch fixtures, results, squads, lineups, injuries, odds (real or seed) → DB.
2. **Calibrate**: fit ratings on `match_results`.
3. **Price**: for each fixture compute `MatchProbs` + markets; de-vig odds; compute EV/edge/
   verdict → `model_snapshots`.
4. **Simulate**: Monte-Carlo tournament → `tournament_snapshot` + group/outright markets.
5. **News**: refresh `team_news`.
API reads only persisted snapshots → fast, deterministic responses.

## 9. Testing & quality

- **Unit**: each algo module against known values (Poisson pmf/cdf, DC tau, Shin de-vig,
  Kelly, EV, score-matrix market derivations sum to 1 within tol).
- **Property**: probabilities in [0,1], market groups sum to ~1, EV sign consistent with edge.
- **Integration**: API endpoints against **Seed providers** (no keys) — full app exercised.
- **Calibration sanity**: model reproduces plausible probabilities on a held set of historical
  matches (e.g. stronger team favored, home advantage positive).
- **Tooling**: `pytest`, `ruff`, `mypy` (best-effort), `.env.example`, `README` run steps.

## 10. Repo layout

```
backend/
  pyproject.toml  .env.example  README.md  alembic.ini
  alembic/versions/
  app/
    main.py  config.py  cli.py
    db/        (session, base, models)
    providers/ (base, the_odds_api, api_football, injuries, rss_news, seed/, cache, factory)
    models/    (ratings, match_model, tournament, player_props, betting)
    services/  (ingestion, pricing, bankroll, news)
    api/       (routes_* )
    schemas/   (pydantic response models)
    seed/      (ported prototype data: teams, matches, squads, history)
  tests/
```

## 11. Delivery phasing (to hit Friday, tested)

1. **Foundations**: repo, config, DB models + migrations, seed data port, provider
   interfaces + seed adapters, `betting.py` + tests.
2. **Model**: `ratings.py`, `match_model.py`, `player_props.py` + tests.
3. **Sim + pricing**: `tournament.py`, pricing/ingestion services + snapshots + tests.
4. **API**: all endpoints on seed data + integration tests → **app fully runnable & tested
   without keys** (the "tested & approved" milestone).
5. **Real adapters**: The Odds API, API-Football, RSS news; validated against seed contract;
   activate via `.env`.

Milestone 4 is the deadline-critical "tested and approved" state; milestone 5 layers real
data on top and is gated only by API keys.
