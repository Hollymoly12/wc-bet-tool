from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.api.deps import DbDep, latest_snapshot
from app.db.models import Match, Team, ModelSnapshot
from app.seed import seed_data
from app.seed.extras import H2H

router = APIRouter()

# Build day/time lookup from seed_data.MATCHES
_MATCH_META: dict[str, dict] = {
    m["id"]: {"day": m["day"], "time": m["time"]}
    for m in seed_data.MATCHES
}


def _enrich_match(payload: dict, match: Match | None, db) -> dict:
    meta = _MATCH_META.get(payload["id"], {"day": "", "time": ""})
    home_team = db.get(Team, payload["home"]) if match else None
    away_team = db.get(Team, payload["away"]) if match else None
    # Prefer kickoff from the snapshot payload (set during ingestion from commence_time),
    # fall back to Match.kickoff DB field (from FixtureDTO), then None.
    kickoff = payload.get("kickoff")
    if kickoff is None and match is not None and match.kickoff is not None:
        kickoff = match.kickoff.isoformat()
    return {
        **payload,
        "homeName": home_team.name if home_team else payload.get("home", ""),
        "awayName": away_team.name if away_team else payload.get("away", ""),
        "group": match.group if match else "",
        "day": meta["day"],
        "time": meta["time"],
        "venue": match.venue if match else "",
        "kickoff": kickoff,
    }


@router.get("/matches")
def get_matches(db: DbDep):
    # Get the latest snapshot for each distinct match ref
    snaps = (
        db.query(ModelSnapshot)
        .filter(ModelSnapshot.kind == "match")
        .order_by(ModelSnapshot.created_at.desc())
        .all()
    )
    # Deduplicate: keep only the latest per ref
    seen: set[str] = set()
    result = []
    for snap in snaps:
        if snap.ref in seen:
            continue
        seen.add(snap.ref)
        match = db.get(Match, snap.ref)
        enriched = _enrich_match(snap.payload, match, db)
        result.append(enriched)
    return result


@router.get("/matches/{match_id}")
def get_match(match_id: str, db: DbDep):
    snap = latest_snapshot(db, "match", match_id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Match not found")
    match = db.get(Match, match_id)
    enriched = _enrich_match(snap.payload, match, db)
    enriched["h2h"] = H2H.get(match_id, [])
    return enriched
