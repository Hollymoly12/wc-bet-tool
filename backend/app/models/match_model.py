"""Dixon-Coles score matrix and every market derived from it."""
from __future__ import annotations
from app.models.poisson import pmf
from app.models.ratings import _dc_tau


def score_matrix(lh: float, la: float, rho: float = -0.05, max_goals: int = 10) -> list[list[float]]:
    M = [[0.0] * (max_goals + 1) for _ in range(max_goals + 1)]
    s = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = pmf(i, lh) * pmf(j, la) * _dc_tau(i, j, lh, la, rho)
            p = max(p, 0.0)
            M[i][j] = p
            s += p
    if s > 0:
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                M[i][j] /= s
    return M


def match_markets(lh: float, la: float, rho: float = -0.05, max_goals: int = 10) -> dict:
    M = score_matrix(lh, la, rho, max_goals)
    home = draw = away = 0.0
    btts_yes = 0.0
    totals = {f"over_{l}": 0.0 for l in (0.5, 1.5, 2.5, 3.5, 4.5)}
    exact = {}
    exp_h = exp_a = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = M[i][j]
            if i > j: home += p
            elif i == j: draw += p
            else: away += p
            if i > 0 and j > 0: btts_yes += p
            exp_h += i * p; exp_a += j * p
            tot = i + j
            for line in (0.5, 1.5, 2.5, 3.5, 4.5):
                if tot > line:
                    totals[f"over_{line}"] += p
            if i <= 5 and j <= 5:
                exact[f"{i}-{j}"] = p
    top_scores = dict(sorted(exact.items(), key=lambda kv: kv[1], reverse=True)[:6])
    return {
        "1x2": {"home": home, "draw": draw, "away": away},
        "double_chance": {"home_draw": home + draw, "home_away": home + away,
                          "draw_away": draw + away},
        "dnb": {"home": home / (home + away) if (home + away) else 0.5,
                "away": away / (home + away) if (home + away) else 0.5},
        "totals": {**{k: v for k, v in totals.items()},
                   **{k.replace("over", "under"): 1 - v for k, v in totals.items()}},
        "btts": {"yes": btts_yes, "no": 1 - btts_yes},
        "exact_score": top_scores,
        "xg": {"home": exp_h, "away": exp_a, "total": exp_h + exp_a},
    }
