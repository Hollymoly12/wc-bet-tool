# backend/tests/test_match_model.py
from app.models.match_model import score_matrix, match_markets


def test_matrix_sums_to_one():
    M = score_matrix(1.6, 1.1, rho=-0.05, max_goals=10)
    total = sum(sum(row) for row in M)
    assert abs(total - 1.0) < 1e-6


def test_markets_1x2_sum_to_one():
    mk = match_markets(1.8, 1.0, rho=-0.05)
    p = mk["1x2"]
    assert abs(p["home"] + p["draw"] + p["away"] - 1.0) < 1e-6
    assert p["home"] > p["away"]  # higher home lambda


def test_over_under_complement():
    mk = match_markets(1.6, 1.2, rho=-0.05)
    assert abs(mk["totals"]["over_2.5"] + mk["totals"]["under_2.5"] - 1.0) < 1e-6


def test_btts_in_unit_interval():
    mk = match_markets(1.6, 1.2, rho=-0.05)
    assert 0 < mk["btts"]["yes"] < 1
    assert abs(mk["btts"]["yes"] + mk["btts"]["no"] - 1.0) < 1e-6
