"""Orchestrates ratings -> match model -> betting into snapshot payloads."""
from __future__ import annotations
import math
from app.models.match_model import match_markets
from app.models import betting as B


def price_match(match_id: str, home: str, away: str, ratings, market_odds: dict) -> dict:
    """Price a single match fixture into a snapshot payload dict."""
    lh, la = ratings.lambdas(home, away)
    mk = match_markets(lh, la, rho=ratings.rho)
    p = mk["1x2"]
    fair = B.fair_probs([market_odds["home"], market_odds["draw"], market_odds["away"]])
    legs = []
    for kind, fairp in zip(("home", "draw", "away"), fair):
        dec = market_odds[kind]
        model = p[kind]
        legs.append({
            "kind": kind,
            "dec": dec,
            "model": model,
            "implied": B.implied_prob(dec),
            "fair": fairp,
            "edge": model - fairp,
            "ev": B.ev(model, dec),
            "kelly": B.kelly_full(model, dec),
            "verdict": B.verdict(model - fairp),
        })
    best = max(legs, key=lambda x: x["ev"])
    return {
        "id": match_id,
        "home": home,
        "away": away,
        "markets": mk,
        "legs": legs,
        "best": best,
        "xg": mk["xg"],
        "conf": B.confidence(max(p.values())),
    }


def price_outright(ratings, dec_by_code: dict) -> list[dict]:
    """Price outright winner market for every team in dec_by_code.

    Model probability is proportional to exp(net_rating * scale);
    fair probability is de-vigged from the book outright column.
    """
    nets = {c: ratings.teams[c].attack - ratings.teams[c].defense for c in dec_by_code}
    z = {c: math.exp(2.2 * nets[c]) for c in nets}
    s = sum(z.values())
    model = {c: z[c] / s for c in z}
    codes = list(dec_by_code)
    fair = B.fair_probs([dec_by_code[c] for c in codes])
    fair_by = dict(zip(codes, fair))
    rows = []
    for c in codes:
        dec = dec_by_code[c]
        m = model[c]
        rows.append({
            "code": c,
            "dec": dec,
            "model": m,
            "implied": B.implied_prob(dec),
            "fair": fair_by[c],
            "edge": m - fair_by[c],
            "ev": B.ev(m, dec),
            "kelly": B.kelly_full(m, dec),
            "verdict": B.verdict(m - fair_by[c]),
            "str": ratings.teams[c].str_rating,
        })
    return rows
