"""Per-player Poisson props scaled by team attacking context."""
from __future__ import annotations
import math
from app.models.poisson import tail_ge

LINE = {"GK": "GK", "RB": "DEF", "CB": "DEF", "LB": "DEF", "RWB": "DEF", "LWB": "DEF",
        "CDM": "MID", "CM": "MID", "CAM": "MID", "DM": "MID", "RM": "MID", "LM": "MID"}
BASE = {
    "FWD": {"g": 0.52, "sh": 3.0, "sot": 1.25, "card": 0.15},
    "MID": {"g": 0.17, "sh": 1.7, "sot": 0.60, "card": 0.22},
    "DEF": {"g": 0.06, "sh": 0.7, "sot": 0.22, "card": 0.30},
    "GK":  {"g": 0.0,  "sh": 0.0, "sot": 0.0,  "card": 0.07},
}


def line_of(pos: str) -> str:
    return LINE.get(pos, "FWD")


def base_rates(pos: str) -> dict:
    return BASE[line_of(pos)]


def _choose_line(lam: float) -> float:
    return 0.5 if lam < 1 else round(lam) - 0.5


def player_props(pos: str, tier: float, team_lambda: float) -> dict:
    b = base_rates(pos)
    atk = team_lambda / 1.6
    gpg = b["g"] * tier * atk
    shg = b["sh"] * tier
    sotg = b["sot"] * tier
    scorer = None if line_of(pos) == "GK" else {"model": 1 - math.exp(-gpg)}
    def over(lam):
        L = _choose_line(lam)
        return {"line": L, "model": tail_ge(int(L + 0.5), lam)}
    return {
        "scorer": scorer,
        "shots": None if line_of(pos) == "GK" else over(shg),
        "sot": None if line_of(pos) == "GK" else over(sotg),
        "card": {"model": min(0.55, b["card"])},
    }
