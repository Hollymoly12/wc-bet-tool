from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.api.deps import DbDep
from app.db.models import Player, Team
from app.models.player_props import player_props

router = APIRouter()


def _team_lambda(str_rating: float) -> float:
    """Approximate team attacking lambda from str_rating. Clamp [0.6, 2.6]."""
    lam = 0.9 + (str_rating - 46) / 24
    return max(0.6, min(2.6, lam))


@router.get("/players")
def list_players(code: str, db: DbDep):
    players = db.query(Player).filter(Player.code == code).all()
    return [
        {"id": p.id, "name": p.name, "pos": p.pos, "number": p.number}
        for p in players
    ]


@router.get("/players/{player_id}")
def get_player(player_id: int, db: DbDep):
    p = db.get(Player, player_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Player not found")
    team = db.get(Team, p.code)
    lam = _team_lambda(team.str_rating if team else 55.0)
    props = player_props(p.pos, p.tier, lam)
    return {
        "id": p.id,
        "code": p.code,
        "team": p.code,
        "number": p.number,
        "name": p.name,
        "pos": p.pos,
        "club": p.club,
        "tier": p.tier,
        "starter": p.starter,
        "props": props,
    }
