from __future__ import annotations
from fastapi import APIRouter
from app.api.deps import DbDep
from app.db.models import Team
from app.seed import seed_data
from app.services.tournament_service import projected_bracket

router = APIRouter()


@router.get("/bracket")
def get_bracket(db: DbDep):
    teams = db.query(Team).all()
    str_by_code = {t.code: t.str_rating for t in teams}
    name_by_code = {t.code: t.name for t in teams}
    group_of = {t.code: t.group for t in teams}

    raw = projected_bracket(str_by_code, group_of)

    # Enrich codes with name
    def enrich(obj: dict | None) -> dict | None:
        if obj is None:
            return None
        return {**obj, "name": name_by_code.get(obj["code"], obj["code"])}

    rounds_out = []
    for r in raw["rounds"]:
        matches_out = []
        for m in r["matches"]:
            matches_out.append({
                "a": enrich(m.get("a")),
                "b": enrich(m.get("b")),
                "winner": enrich(m.get("winner")),
            })
        rounds_out.append({"name": r["name"], "matches": matches_out})

    champion = enrich(raw["champion"])
    return {"rounds": rounds_out, "champion": champion}
