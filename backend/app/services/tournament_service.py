"""Tournament simulation service — builds GroupTeam lists from ratings and runs simulate."""
from __future__ import annotations
from app.models.tournament import simulate, GroupTeam, SimResult


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
