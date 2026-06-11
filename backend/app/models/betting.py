"""Core betting math: pricing, de-vigging, staking, value verdicts."""
from __future__ import annotations

RISK = {
    "conservative": {"label": "Conservative", "mult": 0.25, "cap": 0.04},
    "balanced": {"label": "Balanced", "mult": 0.50, "cap": 0.07},
    "aggressive": {"label": "Aggressive", "mult": 1.00, "cap": 0.12},
}

# Stage-aware staking: group stage = conservative fractional-Kelly; knockouts = larger
STAGE_STAKING = {
    "group":    {"mult": 0.25, "cap": 0.03},
    "knockout": {"mult": 0.50, "cap": 0.07},
}


def implied_prob(dec: float) -> float:
    return 1.0 / dec


def ev(p: float, dec: float) -> float:
    """Expected value per unit staked."""
    return p * dec - 1.0


def kelly_full(p: float, dec: float) -> float:
    b = dec - 1.0
    if b <= 0:
        return 0.0
    f = (b * p - (1 - p)) / b
    return max(0.0, f)


def devig_multiplicative(dec_odds: list[float]) -> list[float]:
    """Normalize raw implied probabilities so they sum to 1."""
    raw = [1.0 / d for d in dec_odds]
    s = sum(raw)
    return [r / s for r in raw]


def devig_shin(dec_odds: list[float], iters: int = 60) -> list[float]:
    """Shin (1992) de-vig: solves for insider-trading proportion z, returns fair probs."""
    pi = [1.0 / d for d in dec_odds]
    booksum = sum(pi)
    z = 0.0
    for _ in range(iters):
        denom = sum(((z * z + 4 * (1 - z) * (p**2) / booksum) ** 0.5) for p in pi)
        z_new = (denom - 2) / (len(pi) - 2) if len(pi) > 2 else 0.0
        if abs(z_new - z) < 1e-9:
            z = z_new
            break
        # Damped update: raw substitution oscillates, averaging ensures convergence
        z = max(0.0, min(0.2, (z + z_new) / 2))
    fair = []
    for p in pi:
        val = ((z * z + 4 * (1 - z) * (p**2) / booksum) ** 0.5 - z) / (2 * (1 - z))
        fair.append(val)
    s = sum(fair)
    return [f / s for f in fair]


def fair_probs(dec_odds: list[float], method: str = "shin") -> list[float]:
    if method == "shin" and len(dec_odds) >= 3:
        try:
            return devig_shin(dec_odds)
        except (ValueError, ZeroDivisionError):
            return devig_multiplicative(dec_odds)
    return devig_multiplicative(dec_odds)


def recommended_stake(p: float, dec: float, bankroll: float, risk: str = "balanced") -> int:
    r = RISK.get(risk, RISK["balanced"])
    raw_f = kelly_full(p, dec) * r["mult"]
    f = min(raw_f, r["cap"])
    stake = int(round(bankroll * f))
    # Ensure a genuine positive-edge bet doesn't silently round to €0
    if stake == 0 and raw_f > 0 and bankroll * f >= 0.5:
        stake = 1
    return stake


def recommended_stake_staged(p: float, dec: float, bankroll: float, stage: str = "group") -> int:
    """Stage-aware staking: group = ¼-Kelly capped 3%; knockout = ½-Kelly capped 7%.

    Outright / non-match bets should use the default 'group' params (conservative).
    """
    params = STAGE_STAKING.get(stage, STAGE_STAKING["group"])
    raw_f = kelly_full(p, dec) * params["mult"]
    f = min(raw_f, params["cap"])
    stake = int(round(bankroll * f))
    # Ensure a genuine positive-edge bet doesn't silently round to €0
    if stake == 0 and raw_f > 0 and bankroll * f >= 0.5:
        stake = 1
    return stake


# Shared value-pick thresholds (used by is_value_pick AND verdict so the two
# stay consistent — a leg that can't be a pick never reads "value"/"strong").
MIN_VALUE_PROB = 0.33
MAX_VALUE_DEC = 4.0
# Minimum edge to count as value/strong. The 1X2 is market-anchored so edges are
# small; require a real ≥1.5% edge (avoids flagging noise as value).
EDGE_VALUE = 0.015
EDGE_STRONG = 0.05


def value_score(p_model: float, fair: float) -> float:
    """Balanced value score: edge × probability.

    Rewards large edges on likely outcomes; penalises longshots with tiny edges.
    """
    return (p_model - fair) * p_model


def is_value_pick(
    p_model: float,
    dec: float,
    fair: float,
    min_prob: float = MIN_VALUE_PROB,
    max_dec: float = MAX_VALUE_DEC,
) -> bool:
    """Return True only when all three filters pass:
    - probability is high enough (≥ min_prob)
    - odds are not longshot territory (≤ max_dec)
    - model has genuine positive edge over fair price
    """
    return p_model >= min_prob and dec <= max_dec and (p_model - fair) >= EDGE_VALUE


def verdict(edge: float, p_model: float | None = None, dec: float | None = None) -> str:
    """edge = p_model - p_fair.

    A leg that can't be a value pick — probability below MIN_VALUE_PROB or odds
    above MAX_VALUE_DEC — never reads 'value'/'strong'; it caps at 'pass'. This
    keeps the verdict consistent with is_value_pick, so a draw/longshot with a
    large but artefactual edge isn't displayed as a recommendation.
    Pass p_model=None to get the original edge-only thresholds (backward compat).
    """
    if edge >= EDGE_STRONG:
        label = "strong"
    elif edge >= EDGE_VALUE:
        label = "value"
    elif edge >= -0.01:
        label = "pass"
    else:
        label = "avoid"
    if p_model is not None:
        not_pickable = p_model < MIN_VALUE_PROB or (dec is not None and dec > MAX_VALUE_DEC)
        if not_pickable and label in ("strong", "value"):
            label = "pass"
        elif p_model < 0.20 and label == "strong":
            label = "value"
    return label


def confidence(model_prob: float, coverage: float = 1.0) -> int:
    """0-100 confidence from distance-from-coinflip and data coverage."""
    sharpness = abs(model_prob - 0.5) * 2  # 0..1
    return int(round(max(0.0, min(1.0, 0.45 + 0.45 * sharpness)) * coverage * 100))
