from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.api.deps import DbDep, latest_snapshot
from app.db.models import Team, Player, TeamNews

router = APIRouter()


@router.get("/teams")
def list_teams(db: DbDep):
    teams = db.query(Team).all()
    return [
        {
            "code": t.code,
            "name": t.name,
            "group": t.group,
            "str": t.str_rating,
            "form": t.form,
            "elo": t.elo,
        }
        for t in teams
    ]


@router.get("/teams/{code}")
def get_team(code: str, db: DbDep):
    team = db.get(Team, code)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    squad = db.query(Player).filter(Player.code == code).all()
    squad_out = [
        {
            "id": p.id,
            "code": p.code,
            "number": p.number,
            "name": p.name,
            "pos": p.pos,
            "club": p.club,
            "tier": p.tier,
            "starter": p.starter,
        }
        for p in squad
    ]

    # Get outright row for this team
    snap = latest_snapshot(db, "outright", "all")
    outright_row = None
    if snap:
        rows = snap.payload.get("rows", [])
        for row in rows:
            if row.get("code") == code:
                outright_row = row
                break

    news = db.query(TeamNews).filter(TeamNews.code == code).all()
    news_out = [
        {
            "tag": n.tag,
            "text": n.text,
            "source": n.source,
            "url": n.url,
            "published_at": n.published_at.isoformat() if n.published_at else None,
        }
        for n in news
    ]

    return {
        "code": team.code,
        "name": team.name,
        "group": team.group,
        "str": team.str_rating,
        "form": team.form,
        "elo": team.elo,
        "colors": team.colors,
        "attack": team.attack,
        "defense": team.defense,
        "squad": squad_out,
        "outright": outright_row,
        "news": news_out,
    }
