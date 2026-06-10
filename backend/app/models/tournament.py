"""Monte-Carlo simulation of the WC2026 group + knockout structure."""
from __future__ import annotations
from dataclasses import dataclass, field
from functools import lru_cache
import math
import numpy as np


def _seeded_slots(n: int = 32) -> list[int]:
    """Standard seeded bracket ordering (1 vs 32, etc). Invariant across sims."""
    slots = [1, 2]
    while len(slots) < n:
        length = len(slots) * 2
        nxt: list[int] = []
        for sidx in slots:
            nxt += [sidx, length + 1 - sidx]
        slots = nxt
    return slots


_ROUND_KEYS = ["r16", "qf", "sf", "final", "champ"]
_BRACKET_SLOTS = _seeded_slots(32)


@dataclass
class GroupTeam:
    code: str
    str_rating: float


@dataclass
class SimResult:
    team_probs: dict[str, dict]
    group_winner: dict[str, dict]
    champion: dict[str, float]
    qualifiers_example: list[str] = field(default_factory=list)


@lru_cache(maxsize=None)
def _pair_probs(sa: float, sb: float) -> tuple[float, float, float]:
    diff = sa - sb
    pa = 1 / (1 + 10 ** (-diff / 24))
    dr = min(0.30, max(0.09, 0.28 * math.exp(-abs(diff) / 46)))
    return (1 - dr) * pa, (1 - dr) * (1 - pa), dr


def simulate(groups: dict[str, list[GroupTeam]], sims: int = 50000, seed: int = 42) -> SimResult:
    rng = np.random.default_rng(seed)
    letters = list(groups.keys())
    all_codes = [t.code for g in groups.values() for t in g]
    counts = {c: {"win": 0, "qualify": 0, "r16": 0, "qf": 0, "sf": 0, "final": 0, "champ": 0}
              for c in all_codes}
    gw_counts = {L: {t.code: 0 for t in groups[L]} for L in letters}

    for _ in range(sims):
        winners, runners, thirds = [], [], []
        for L in letters:
            g = groups[L]
            pts = {t.code: 0 for t in g}
            gd = {t.code: 0 for t in g}
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    a, b = g[i], g[j]
                    wa, wb, _ = _pair_probs(a.str_rating, b.str_rating)
                    r = rng.random()
                    if r < wa: pts[a.code] += 3; gd[a.code] += 1; gd[b.code] -= 1
                    elif r < wa + wb: pts[b.code] += 3; gd[b.code] += 1; gd[a.code] -= 1
                    else: pts[a.code] += 1; pts[b.code] += 1
            order = sorted(g, key=lambda t: (pts[t.code], gd[t.code], t.str_rating,
                                             rng.random()), reverse=True)
            gw_counts[L][order[0].code] += 1
            counts[order[0].code]["qualify"] += 1
            counts[order[1].code]["qualify"] += 1
            winners.append(order[0]); runners.append(order[1]); thirds.append(order[2])
        best_thirds = sorted(thirds, key=lambda t: t.str_rating, reverse=True)[:8]
        bracket = sorted(winners + runners + best_thirds,
                         key=lambda t: t.str_rating, reverse=True)
        current = [bracket[s - 1] for s in _BRACKET_SLOTS]
        ridx = 0
        while len(current) > 1:
            nxt = []
            for k in range(0, len(current), 2):
                a, b = current[k], current[k + 1]
                wa, wb, _ = _pair_probs(a.str_rating, b.str_rating)
                tot = wa + wb or 1
                w = a if rng.random() < wa / tot else b
                nxt.append(w)
            for w in nxt:
                if ridx < len(_ROUND_KEYS):
                    counts[w.code][_ROUND_KEYS[ridx]] += 1
            current = nxt; ridx += 1
        champ = current[0]
        counts[champ.code]["win"] += 1

    team_probs = {c: {k: counts[c][k] / sims for k in counts[c]} for c in all_codes}
    group_winner = {L: {c: gw_counts[L][c] / sims for c in gw_counts[L]} for L in letters}
    champion = {c: team_probs[c]["champ"] for c in all_codes}
    return SimResult(team_probs=team_probs, group_winner=group_winner, champion=champion)
