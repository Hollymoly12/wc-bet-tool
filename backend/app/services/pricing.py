"""Orchestrates ratings -> match model -> betting into snapshot payloads."""
from __future__ import annotations
from app.models.match_model import match_markets
from app.models import betting as B
from app.services.market_anchor import lambdas_from_strength
# Re-exported for backward compatibility; the implementations live in the
# scipy-free market_util module so the read API can import them standalone.
from app.services.market_util import _shash, market_from_prob  # noqa: F401

# Weight of the independent strength→Poisson model in the match 1X2 (the rest is
# the de-vigged market). Keeps the model honest without letting its blowout
# miscalibration produce artefactual value on draws/underdogs.
MATCH_MODEL_WEIGHT = 0.50


def price_match(
    match_id: str,
    home: str,
    away: str,
    ratings,
    market_odds: dict,
    str_by_code: dict[str, float],
    stage: str = "group",
) -> dict:
    """Price a single match fixture into a snapshot payload dict.

    Lambdas come from blended market-anchored strengths via
    lambdas_from_strength, NOT from ratings.lambdas().  rho is taken
    from the fitted ratings model (or -0.05 if no ratings).

    ``stage`` is "group" or "knockout" — used for stage-aware staking and
    surfaced in the payload so the frontend can display the right staking label.
    """
    sH = str_by_code[home]
    sA = str_by_code[away]
    rho_value = ratings.rho if ratings is not None else -0.05
    lh, la = lambdas_from_strength(sH, sA)
    mk = match_markets(lh, la, rho=rho_value)
    fair = B.fair_probs([market_odds["home"], market_odds["draw"], market_odds["away"]])
    # Market-anchor the 1X2. The pure strength→Poisson model is miscalibrated for
    # big mismatches (it overrates draws/underdogs → artefactual +EV). Blend it
    # toward the de-vigged market so probabilities and EVs are realistic; genuine
    # divergences survive (smaller, honest edges).
    _kinds = ("home", "draw", "away")
    _fairmap = dict(zip(_kinds, fair))
    p = {k: MATCH_MODEL_WEIGHT * mk["1x2"][k] + (1 - MATCH_MODEL_WEIGHT) * _fairmap[k]
         for k in _kinds}
    mk["1x2"] = p  # keep displayed market consistent with the anchored legs
    legs = []
    for kind, fairp in zip(_kinds, fair):
        dec = market_odds[kind]
        model = p[kind]
        ev = B.ev(model, dec)
        legs.append({
            "kind": kind,
            "dec": dec,
            "model": model,
            "implied": B.implied_prob(dec),
            "fair": fairp,
            "edge": model - fairp,
            "ev": ev,
            "kelly": B.kelly_full(model, dec),
            "verdict": B.verdict(ev, model, dec),
            "value_score": B.value_score(model, dec),
            "is_value": B.is_value_pick(model, dec),
        })
    # Best = highest value_score among legs that pass the value-pick filter.
    # Falls back to None if no leg passes (no recommended pick for this match).
    value_legs = [leg for leg in legs if leg["is_value"]]
    best: dict | None = (
        max(value_legs, key=lambda x: x["value_score"]) if value_legs else None
    )
    return {
        "id": match_id,
        "home": home,
        "away": away,
        "stage": stage,
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
        ev = B.ev(m, dec)
        rows.append({
            "code": c,
            "dec": dec,
            "model": m,
            "implied": B.implied_prob(dec),
            "fair": fair_by[c],
            "edge": m - fair_by[c],
            "ev": ev,
            "kelly": B.kelly_full(m, dec),
            "verdict": B.verdict(ev, m, dec),
            "value_score": B.value_score(m, dec),
            "is_value": B.is_value_pick(m, dec),
            "str": str_by_code.get(c, 55.0),
        })
    return rows
