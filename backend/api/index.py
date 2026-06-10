"""Slim ASGI app for Vercel serverless deployment.

Includes only the read-only routers that do NOT transitively import scipy/numpy
at module load time.  Heavy model code (ratings, match_model, tournament) is
loaded lazily inside individual route handlers where needed — see
routes_groups.py and routes_bracket.py for the deferred-import wrappers.

Routers included:
  /meta         — risk config (pure Python)
  /outright     — DB read + Team enrichment
  /matches      — DB read + seed metadata
  /groups       — DB read + market_from_prob (lazy scipy chain)
  /bracket      — DB read + projected_bracket (lazy numpy chain)
  /teams        — DB read
  /players      — DB read + player_props (pure Poisson, no scipy)
  /news         — DB read
  /bankroll     — DB read/write

Excluded:
  /admin/refresh  — triggers full ingestion pipeline (scipy + httpx + feedparser)
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_meta import router as meta_router
from app.api.routes_outright import router as outright_router
from app.api.routes_matches import router as matches_router
from app.api.routes_groups import router as groups_router
from app.api.routes_bracket import router as bracket_router
from app.api.routes_teams import router as teams_router
from app.api.routes_players import router as players_router
from app.api.routes_news import router as news_router
from app.api.routes_bankroll import router as bankroll_router

app = FastAPI(title="WC Bet Tool Read API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta_router)
app.include_router(outright_router)
app.include_router(matches_router)
app.include_router(groups_router)
app.include_router(bracket_router)
app.include_router(teams_router)
app.include_router(players_router)
app.include_router(news_router)
app.include_router(bankroll_router)
