"""Market-anchored strength model.

Anchors team strength to de-vigged outright market odds while letting
the Dixon-Coles model provide a small nudge where data is rich.
This prevents confederation-siloed noise from producing degenerate
predictions (e.g. Saudi Arabia 27% WC win, minnows beating favourites).
"""
from __future__ import annotations

import math

SCALE = 8.0           # strength points per "1.0 supremacy unit"
K = 0.5               # supremacy gain
BASE_TOTAL = 2.6      # baseline total goals per match
HOME_ADV_GOALS = 0.2
MODEL_MAX_WEIGHT = 0.35    # model can contribute at most 35% of the blend
CONF_MATCHES = 15.0        # matches needed for full model confidence


def _zscores(values: dict[str, float]) -> dict[str, float]:
    """Return z-score map; if std==0 return zeros."""
    xs = list(values.values())
    n = len(xs)
    if n == 0:
        return {}
    mu = sum(xs) / n
    var = sum((x - mu) ** 2 for x in xs) / n
    sd = var ** 0.5
    if sd == 0:
        return {k: 0.0 for k in values}
    return {k: (v - mu) / sd for k, v in values.items()}


def market_strength_z(outright_dec_by_code: dict[str, float]) -> dict[str, float]:
    """De-vig outright odds -> fair champion prob -> z-scored log-prob.

    This produces a sane cross-confederation strength proxy: teams with
    short (low) outright odds get high z-scores, long shots get low ones,
    and the ranking is purely market-derived (avoiding model noise).
    """
    from app.models import betting as B  # local import to avoid circular

    codes = list(outright_dec_by_code)
    if not codes:
        return {}
    fair = B.fair_probs([outright_dec_by_code[c] for c in codes])
    q = {c: max(p, 1e-6) for c, p in zip(codes, fair)}
    logq = {c: math.log(q[c]) for c in codes}
    return _zscores(logq)


def blended_strength(
    model_net: dict[str, float],
    market_dec: dict[str, float],
    n_matches: dict[str, int],
    codes: list[str],
) -> dict[str, float]:
    """Return str_rating in [48, 96] per code: blend market z (anchor) with model z (nudge).

    For teams with few calibration matches the blend is almost entirely
    market-anchored; for data-rich teams the model can nudge up to
    MODEL_MAX_WEIGHT (35%) of the final z-score.
    """
    zmkt = market_strength_z(market_dec)
    zmod = _zscores({c: model_net.get(c, 0.0) for c in codes})
    out = {}
    for c in codes:
        conf = min(1.0, n_matches.get(c, 0) / CONF_MATCHES)
        w = MODEL_MAX_WEIGHT * conf
        z = w * zmod.get(c, 0.0) + (1 - w) * zmkt.get(c, 0.0)
        s = 72.0 + 11.0 * z
        out[c] = max(48.0, min(96.0, s))
    return out


def lambdas_from_strength(
    sH: float,
    sA: float,
    home_adv_goals: float = HOME_ADV_GOALS,
) -> tuple[float, float]:
    """Map blended strengths -> (lambda_home, lambda_away) with realistic totals.

    Returns expected goals per side.  For equal strengths the total is
    BASE_TOTAL (2.6); home advantage adds HOME_ADV_GOALS to lh and
    subtracts from la.  A 40-point supremacy gap floors la near 0.15
    and caps lh near 4.0.
    """
    diff = (sH - sA) / SCALE
    sup = K * diff + home_adv_goals
    lh = max(0.15, min(4.0, BASE_TOTAL / 2 + sup / 2))
    la = max(0.15, min(4.0, BASE_TOTAL / 2 - sup / 2))
    return lh, la
