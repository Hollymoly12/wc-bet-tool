# EDGE WC26 — Frontend

React + Vite frontend for the World Cup Bet Tool.

## Local development

```bash
cd frontend
npm install
```

Set the API URL (defaults to `http://localhost:8000`):

```bash
export VITE_API_URL=http://localhost:8000
# or create a .env.local file:
echo "VITE_API_URL=http://localhost:8000" > .env.local
```

Start the backend first (seed mode, no API keys needed):

```bash
cd ../backend
.venv/bin/python -m app.cli init-db
.venv/bin/python -m app.cli refresh
.venv/bin/uvicorn app.main:app --port 8000
```

Then run the frontend dev server:

```bash
cd frontend
npm run dev
# Opens on http://localhost:5173
```

## Build

```bash
npm run build
# Outputs to frontend/dist/
```

## Deploy to Vercel

1. Push the repo to GitHub.
2. Import the repo in Vercel, set **Root Directory** to `frontend`.
3. Set the environment variable:
   - `VITE_API_URL` = `https://your-deployed-backend.vercel.app`
     (or wherever the FastAPI backend is hosted)
4. Vercel auto-detects Vite. The `vercel.json` adds the SPA rewrite for client-side routing.

## Screens

| Screen | Status |
|--------|--------|
| Dashboard | Fully wired — top value play, bankroll snapshot, leaderboard, upcoming fixtures |
| Outright Board | Fully wired — sortable table, EV/confidence, bet staging |
| Match Analysis | Fully wired — 1X2 outcomes, markets table, H2H, model read |
| Groups | Fully wired — 12 group cards, win/qualify bet chips |
| Bracket | Fully wired — projected knockout rounds |
| Team Stats | Wired — ELO/strength table (simplified; no player props) |
| Team Detail | Wired — fetches on navigate, squad list, fixtures, news |
| Bankroll | Wired — open + settled bets, settle/void actions |
