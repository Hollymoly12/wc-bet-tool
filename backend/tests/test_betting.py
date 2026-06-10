from app.models import betting as B

def test_implied_and_ev():
    assert abs(B.implied_prob(2.0) - 0.5) < 1e-12
    assert abs(B.ev(0.6, 2.0) - 0.2) < 1e-12   # 0.6*2 - 1

def test_kelly_full_and_zero_floor():
    # p=0.6 dec=2.0 -> b=1 -> (1*0.6-0.4)/1 = 0.2
    assert abs(B.kelly_full(0.6, 2.0) - 0.2) < 1e-12
    # no edge -> non-positive kelly floored at 0
    assert B.kelly_full(0.4, 2.0) == 0.0

def test_devig_multiplicative_sums_to_one():
    fair = B.devig_multiplicative([1/0.5, 1/0.3, 1/0.25])  # overround book
    assert abs(sum(fair) - 1.0) < 1e-9
    assert fair[0] > fair[1] > fair[2]

def test_devig_shin_sums_to_one_and_reduces_favorite_bias():
    odds = [1.5, 4.2, 7.0]
    fair = B.devig_shin(odds)
    assert abs(sum(fair) - 1.0) < 1e-6
    # all in (0,1)
    assert all(0 < p < 1 for p in fair)

def test_recommended_stake_caps_and_rounds():
    # huge kelly should be capped by profile cap, rounded to nearest 1
    stake = B.recommended_stake(p=0.9, dec=3.0, bankroll=1000, risk="conservative")
    assert stake <= 1000 * 0.04  # conservative cap
    assert stake == int(stake)   # always a whole number (int)

def test_verdict_thresholds():
    assert B.verdict(0.12) == "strong"
    assert B.verdict(0.05) == "value"
    assert B.verdict(0.0) == "pass"
    assert B.verdict(-0.05) == "avoid"
