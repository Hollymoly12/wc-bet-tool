"""Tournament simulation service — builds GroupTeam lists from ratings and runs simulate."""
from __future__ import annotations
from dataclasses import dataclass
from app.models.tournament import simulate, GroupTeam, SimResult, _pair_probs, _BRACKET_SLOTS
from app.seed import seed_data


ROUND_NAMES = ["Round of 32", "Round of 16", "Quarter-finals", "Semi-finals", "Final"]


@dataclass
class _BTeam:
    code: str
    str_rating: float


def projected_bracket(str_by_code: dict[str, float], group_of: dict[str, str]) -> dict:
    """Build a deterministic projected bracket from team str ratings.

    Returns a dict matching the BracketResponse schema:
      {rounds: [{name, matches: [{a, b, winner}]}], champion}
    """
    # 1. Group teams by letter
    groups: dict[str, list[_BTeam]] = {}
    for code, letter in group_of.items():
        groups.setdefault(letter, []).append(_BTeam(code=code, str_rating=str_by_code.get(code, 55.0)))

    # 2. Sort each group by str_rating, pick winner (idx 0), runner (idx 1), third (idx 2)
    winners: list[_BTeam] = []
    runners: list[_BTeam] = []
    thirds: list[_BTeam] = []
    for letter in sorted(groups.keys()):
        ranked = sorted(groups[letter], key=lambda t: t.str_rating, reverse=True)
        winners.append(ranked[0])
        runners.append(ranked[1])
        thirds.append(ranked[2] if len(ranked) > 2 else ranked[-1])

    # 3. Best 8 third-placed
    best_thirds = sorted(thirds, key=lambda t: t.str_rating, reverse=True)[:8]

    # 4. Seed into bracket slots by str desc
    all32 = sorted(winners + runners + best_thirds, key=lambda t: t.str_rating, reverse=True)
    current: list[_BTeam] = [all32[s - 1] for s in _BRACKET_SLOTS]

    rounds_out = []
    ridx = 0
    while len(current) > 1:
        round_matches = []
        nxt: list[_BTeam] = []
        for k in range(0, len(current), 2):
            a, b = current[k], current[k + 1]
            wa, wb, _ = _pair_probs(a.str_rating, b.str_rating)
            tot = wa + wb or 1.0
            win_prob_a = wa / tot
            win_prob_b = wb / tot
            winner = a if win_prob_a >= win_prob_b else b
            win_prob = max(win_prob_a, win_prob_b)
            round_matches.append({
                "a": {"code": a.code, "str": a.str_rating, "winProb": round(win_prob_a, 4)},
                "b": {"code": b.code, "str": b.str_rating, "winProb": round(win_prob_b, 4)},
                "winner": {"code": winner.code, "str": winner.str_rating, "winProb": round(win_prob, 4)},
            })
            nxt.append(winner)
        name = ROUND_NAMES[ridx] if ridx < len(ROUND_NAMES) else f"Round {ridx + 1}"
        rounds_out.append({"name": name, "matches": round_matches})
        current = nxt
        ridx += 1

    champion = current[0] if current else None
    champion_out = {"code": champion.code, "str": champion.str_rating, "winProb": 1.0} if champion else None
    return {"rounds": rounds_out, "champion": champion_out}


def run_tournament(ratings, group_of: dict[str, str], sims: int = 50000) -> SimResult:
    """Run Monte-Carlo tournament simulation.

    Args:
        ratings: RatingsModel from fit_ratings
        group_of: mapping of team code -> group letter (e.g. {"ESP": "B", ...})
        sims: number of Monte-Carlo iterations

    Returns:
        SimResult with team_probs, group_winner, champion dicts
    """
    groups: dict[str, list[GroupTeam]] = {}
    for code, letter in group_of.items():
        groups.setdefault(letter, []).append(
            GroupTeam(code=code, str_rating=ratings.teams[code].str_rating)
        )
    return simulate(groups, sims=sims)
