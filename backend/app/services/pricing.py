"""Orchestrates ratings -> match model -> betting into snapshot payloads."""
from __future__ import annotations
import math
from app.models.match_model import match_markets
from app.models import betting as B
from app.services.market_anchor import lambdas_from_strength


def _shash(s: str) -> int:
    """Stable (non-salted) string hash for deterministic seeding."""
    h = 0
    for i, c in enumerate(s):
        h += ord(c) * (31 ** i)
    return h


def market_from_prob(prob: float, seed: str) -> dict:
    """Build a simple market dict from a model probability with a small margin.

    margin = 0.90 + (stable_hash(seed) % 22) / 100  → range [0.90, 1.12]
    dec = (1 / max(prob, 0.001)) * margin
    """
    prob = max(prob, 1e-3)
    margin = 0.90 + (_shash(seed) % 22) / 100
    dec = round((1 / prob) * margin, 2)
    dec = max(dec, 1.01)
    implied = round(1 / dec, 6)
    ev = round(prob * dec - 1, 6)
    return {"dec": dec, "implied": implied, "model": prob, "ev": ev}


def price_match(
    match_id: str,
    home: str,
    away: str,
    ratings,
    market_odds: dict,
    str_by_code: dict[str, float],
) -> dict:
    """Price a single match fixture into a snapshot payload dict.

    Lambdas come from blended market-anchored strengths via
    lambdas_from_strength, NOT from ratings.lambdas().  rho is taken
    from the fitted ratings model (or -0.05 if no ratings).
    """
    sH = str_by_code[home]
    sA = str_by_code[away]
    rho_value = ratings.rho if ratings is not None else -0.05
    lh, la = lambdas_from_strength(sH, sA)
    mk = match_markets(lh, la, rho=rho_value)
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


def price_outright(
    champion_probs: dict[str, float],
    dec_by_code: dict[str, float],
    str_by_code: dict[str, float],
) -> list[dict]:
    """Price outright winner market for every team in dec_by_code.

    Model probability comes directly from the tournament simulation's
    champion probabilities (already bounded and summing ≈ 1).
    Fair probability is de-vigged from the book outright column.
    str comes from blended_strength.
    """
    codes = list(dec_by_code)
    fair = B.fair_probs([dec_by_code[c] for c in codes])
    fair_by = dict(zip(codes, fair))
    rows = []
    for c in codes:
        dec = dec_by_code[c]
        m = champion_probs.get(c, 0.0)
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
            "str": str_by_code.get(c, 55.0),
        })
    return rows


# ---------------------------------------------------------------------------
# Legacy helpers kept for internal use only
# ---------------------------------------------------------------------------

def _price_outright_from_ratings(ratings, dec_by_code: dict) -> list[dict]:
    """Legacy: model probability from exp(net_rating * scale).

    Kept for backward compat with tests that don't have sim champion probs.
    Do not use in production pipeline.
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
