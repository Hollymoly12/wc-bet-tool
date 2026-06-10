from __future__ import annotations
from fastapi import APIRouter
from app.api.deps import DbDep, latest_snapshot
from app.db.models import Team

router = APIRouter()


@router.get("/outright")
def get_outright(db: DbDep):
    snap = latest_snapshot(db, "outright", "all")
    if snap is None:
        return []
    rows = snap.payload.get("rows", [])
    # Enrich with name, group, colors from Team table
    enriched = []
    for row in rows:
        team = db.get(Team, row["code"])
        enriched.append({
            **row,
            "name": team.name if team else row["code"],
            "group": team.group if team else "",
            "colors": team.colors if team else [],
        })
    # Sort by model prob desc
    enriched.sort(key=lambda r: r.get("model", 0), reverse=True)
    return enriched
