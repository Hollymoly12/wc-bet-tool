"""Dixon-Coles attack/defense ratings fitted by weighted MLE, plus an Elo fallback."""
from __future__ import annotations
from dataclasses import dataclass, field
import math
import numpy as np
from scipy.optimize import minimize


@dataclass
class TeamRatings:
    attack: float
    defense: float
    elo: float = 1500.0
    str_rating: float = 55.0


@dataclass
class RatingsModel:
    teams: dict[str, TeamRatings]
    home_adv: float
    rho: float
    base: float
    idx: dict[str, int] = field(default_factory=dict)

    def lambdas(self, home: str, away: str) -> tuple[float, float]:
        th, ta = self.teams[home], self.teams[away]
        lh = math.exp(self.base + self.home_adv + th.attack - ta.defense)
        la = math.exp(self.base + ta.attack - th.defense)
        return lh, la


def _decay_weight(days_ago: float, halflife_days: float) -> float:
    return 0.5 ** (days_ago / halflife_days)


def _dc_tau(hg: int, ag: int, lh: float, la: float, rho: float) -> float:
    if hg == 0 and ag == 0:
        return 1 - lh * la * rho
    if hg == 0 and ag == 1:
        return 1 + lh * rho
    if hg == 1 and ag == 0:
        return 1 + la * rho
    if hg == 1 and ag == 1:
        return 1 - rho
    return 1.0


def fit_ratings(history: list[dict], codes: list[str], halflife_days: float = 540.0) -> RatingsModel:
    idx = {c: i for i, c in enumerate(codes)}
    n = len(codes)
    rows = [h for h in history if h["home"] in idx and h["away"] in idx]
    weights = np.array([_decay_weight(h.get("days_ago", 0), halflife_days) for h in rows])

    def unpack(params):
        atk = params[:n]
        df = params[n:2 * n]
        home_adv = params[2 * n]
        rho = params[2 * n + 1]
        base = params[2 * n + 2]
        return atk, df, home_adv, rho, base

    def neg_loglik(params):
        atk, df, home_adv, rho, base = unpack(params)
        # identifiability: center attack
        atk = atk - atk.mean()
        df = df - df.mean()
        ll = 0.0
        for w, h in zip(weights, rows):
            i, j = idx[h["home"]], idx[h["away"]]
            lh = math.exp(base + home_adv + atk[i] - df[j])
            la = math.exp(base + atk[j] - df[i])
            hg, ag = h["home_goals"], h["away_goals"]
            tau = _dc_tau(hg, ag, lh, la, rho)
            tau = max(tau, 1e-6)
            term = (-lh + hg * math.log(lh) - math.lgamma(hg + 1)
                    - la + ag * math.log(la) - math.lgamma(ag + 1) + math.log(tau))
            ll += w * term
        return -ll

    x0 = np.concatenate([np.zeros(n), np.zeros(n), [0.25, -0.05, 0.0]])
    res = minimize(neg_loglik, x0, method="L-BFGS-B",
                   bounds=[(-3, 3)] * (2 * n) + [(-0.5, 1.0), (-0.2, 0.2), (-1.0, 1.5)])
    atk, df, home_adv, rho, base = unpack(res.x)
    atk = atk - atk.mean(); df = df - df.mean()
    teams = {}
    nets = atk - df
    lo, hi = float(nets.min()), float(nets.max())
    for c in codes:
        i = idx[c]
        net = nets[i]
        strv = 50 + 45 * ((net - lo) / (hi - lo)) if hi > lo else 70.0
        teams[c] = TeamRatings(attack=float(atk[i]), defense=float(df[i]),
                               elo=1500.0 + 200 * net, str_rating=float(strv))
    return RatingsModel(teams=teams, home_adv=float(home_adv), rho=float(rho),
                        base=float(base), idx=idx)
