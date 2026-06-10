"""FastAPI application — includes all routers and CORS config."""
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
from app.api.routes_admin import router as admin_router

app = FastAPI(title="WC Bet Tool API", version="0.1.0")

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
app.include_router(admin_router)
