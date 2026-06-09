# backend/tests/test_player_props.py
from app.models.player_props import player_props, base_rates


def test_base_rates_by_line():
    assert base_rates("ST")["g"] > base_rates("CB")["g"]


def test_scorer_prob_increases_with_team_lambda():
    p_low = player_props("ST", tier=1.3, team_lambda=1.0)["scorer"]["model"]
    p_high = player_props("ST", tier=1.3, team_lambda=2.2)["scorer"]["model"]
    assert p_high > p_low
    assert 0 < p_low < 1


def test_gk_has_no_scorer_market():
    assert player_props("GK", tier=1.0, team_lambda=1.5)["scorer"] is None
