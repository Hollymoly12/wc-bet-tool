# backend/tests/test_tournament.py
from app.models.tournament import simulate, GroupTeam


def _groups():
    # 12 groups of 4 with a clear seed ordering by strength
    groups = {}
    s = 90
    for L in "ABCDEFGHIJKL":
        groups[L] = [GroupTeam(code=f"{L}{k}", str_rating=s - k * 8) for k in range(4)]
    return groups


def test_probabilities_sum_per_team_bounded():
    res = simulate(_groups(), sims=2000, seed=1)
    for code, p in res.team_probs.items():
        assert 0 <= p["win"] <= 1
        assert 0 <= p["qualify"] <= 1
        assert p["qualify"] >= p["win"]  # qualifying is easier than winning it all


def test_group_winner_probs_sum_to_one_per_group():
    res = simulate(_groups(), sims=2000, seed=1)
    for L in "ABCDEFGHIJKL":
        s = sum(res.group_winner[L].values())
        assert abs(s - 1.0) < 1e-9


def test_champion_probs_sum_to_one():
    res = simulate(_groups(), sims=2000, seed=1)
    assert abs(sum(res.champion.values()) - 1.0) < 1e-9
