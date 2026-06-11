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
    # EV-based thresholds (no p_model context): strong >= 0.08, value >= 0.01
    assert B.verdict(0.10) == "strong"
    assert B.verdict(0.03) == "value"
    assert B.verdict(0.0) == "pass"
    assert B.verdict(-0.05) == "avoid"

def test_verdict_gated_by_value_filter():
    # A low-probability leg (< MIN_VALUE_PROB) never reads value/strong → 'pass',
    # even with a large (artefactual) edge.
    assert B.verdict(0.15, p_model=0.12) == "pass"
    assert B.verdict(0.10, p_model=0.19) == "pass"
    # High odds (dec > MAX_VALUE_DEC) also caps to 'pass' even with high prob.
    assert B.verdict(0.10, p_model=0.50, dec=5.0) == "pass"
    # A genuine pick (prob ok, odds ok, real edge) keeps its value verdict.
    assert B.verdict(0.03, p_model=0.50, dec=2.0) == "value"

def test_verdict_strong_when_high_prob():
    # A high-probability outcome with large edge should still be 'strong'
    assert B.verdict(0.15, p_model=0.55) == "strong"

def test_value_score():
    # value_score = expected value at offered odds = p_model * dec - 1
    assert abs(B.value_score(0.55, 2.0) - 0.10) < 1e-9
    # Negative EV → negative score
    assert B.value_score(0.40, 2.0) < 0.0

def test_is_value_pick_passes():
    # Favorite profitable at offered odds: p=0.55, dec=1.9 → EV=+0.045 → passes all
    assert B.is_value_pick(0.55, 1.9) is True

def test_is_value_pick_fails_low_prob():
    # p < 0.33 → rejected
    assert B.is_value_pick(0.25, 2.0) is False

def test_is_value_pick_fails_high_dec():
    # dec > 4.0 → longshot, rejected
    assert B.is_value_pick(0.40, 4.5) is False

def test_is_value_pick_fails_negative_ev():
    # p=0.45, dec=2.0 → EV = -0.10 < 0 → not profitable, rejected even though prob ok
    assert B.is_value_pick(0.45, 2.0) is False

def test_recommended_stake_staged_group():
    # Group: ¼-Kelly, cap 3%
    stake = B.recommended_stake_staged(p=0.9, dec=3.0, bankroll=1000, stage="group")
    assert stake <= 1000 * 0.03  # group cap
    assert stake >= 1             # genuine edge should be non-zero

def test_recommended_stake_staged_knockout():
    # Knockout: ½-Kelly, cap 7%
    stake = B.recommended_stake_staged(p=0.9, dec=3.0, bankroll=1000, stage="knockout")
    assert stake <= 1000 * 0.07  # knockout cap
    assert stake >= 1

def test_recommended_stake_staged_knockout_larger_than_group():
    # Same edge → knockout stake should be ≥ group stake
    g = B.recommended_stake_staged(p=0.6, dec=2.0, bankroll=1000, stage="group")
    k = B.recommended_stake_staged(p=0.6, dec=2.0, bankroll=1000, stage="knockout")
    assert k >= g
