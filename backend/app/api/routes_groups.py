from __future__ import annotations
from fastapi import APIRouter
from app.api.deps import DbDep, latest_tournament_snapshot
from app.db.models import Team
from app.seed import seed_data
from app.services.pricing import market_from_prob

router = APIRouter()


@router.get("/groups")
def get_groups(db: DbDep):
    ts = latest_tournament_snapshot(db)
    team_probs: dict = {}
    group_winner: dict = {}
    if ts is not None:
        team_probs = ts.payload.get("team_probs", {})
        group_winner = ts.payload.get("group_winner", {})

    # Build group -> teams map
    groups: dict[str, list] = {}
    teams = db.query(Team).all()
    for t in teams:
        groups.setdefault(t.group, []).append(t)

    result = []
    for letter in sorted(groups.keys()):
        group_teams = groups[letter]
        gw_probs = group_winner.get(letter, {})

        rows = []
        for t in group_teams:
            tp = team_probs.get(t.code, {})
            gw_prob = float(gw_probs.get(t.code, 0.0))
            qual_prob = float(tp.get("qualify", 0.0))
            # third prob: teams can qualify as best third; we don't have clean 3rd prob
            third_prob = 0.0

            gw_market = market_from_prob(gw_prob, f"{letter}:{t.code}:gw")
            qual_market = market_from_prob(qual_prob, f"{letter}:{t.code}:qual")

            rows.append({
                "code": t.code,
                "name": t.name,
                "group": t.group,
                "str": t.str_rating,
                "form": t.form,
                "gwProb": round(gw_prob, 4),
                "qualProb": round(qual_prob, 4),
                "thirdProb": third_prob,
                "gwMarket": gw_market,
                "qualMarket": qual_market,
            })

        # Sort by gwProb desc and assign projRank
        rows.sort(key=lambda r: r["gwProb"], reverse=True)
        for i, row in enumerate(rows):
            row["projRank"] = i + 1

        result.append({"letter": letter, "rows": rows})

    return result
