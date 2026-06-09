"""Core betting math: pricing, de-vigging, staking, value verdicts."""
from __future__ import annotations

RISK = {
    "conservative": {"label": "Conservative", "mult": 0.25, "cap": 0.04},
    "balanced": {"label": "Balanced", "mult": 0.50, "cap": 0.07},
    "aggressive": {"label": "Aggressive", "mult": 1.00, "cap": 0.12},
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
        if abs(z_new - z) < 1e-12:
            z = z_new
            break
        z = max(0.0, min(0.2, z_new))
    fair = []
    for p in pi:
        val = ((z * z + 4 * (1 - z) * (p**2) / booksum) ** 0.5 - z) / (2 * (1 - z))
        fair.append(val)
    s = sum(fair)
    return [f / s for f in fair]


def fair_probs(dec_odds: list[float], method: str = "shin") -> list[float]:
    if method == "shin" and len(dec_odds) >= 2:
        try:
            return devig_shin(dec_odds)
        except (ValueError, ZeroDivisionError):
            return devig_multiplicative(dec_odds)
    return devig_multiplicative(dec_odds)


def recommended_stake(p: float, dec: float, bankroll: float, risk: str = "balanced") -> int:
    r = RISK.get(risk, RISK["balanced"])
    f = min(kelly_full(p, dec) * r["mult"], r["cap"])
    return int(round((bankroll * f) / 5.0)) * 5


def verdict(edge: float) -> str:
    """edge = p_model - p_fair."""
    if edge >= 0.10:
        return "strong"
    if edge >= 0.03:
        return "value"
    if edge >= -0.01:
        return "pass"
    return "avoid"


def confidence(model_prob: float, coverage: float = 1.0) -> int:
    """0-100 confidence from distance-from-coinflip and data coverage."""
    sharpness = abs(model_prob - 0.5) * 2  # 0..1
    return int(round(max(0.0, min(1.0, 0.45 + 0.45 * sharpness)) * coverage * 100))
