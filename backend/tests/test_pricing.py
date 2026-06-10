"""Tests for app.services.pricing."""
from app.services.pricing import price_match, price_outright
from app.models.ratings import fit_ratings
from app.seed import seed_data
from app.services.market_anchor import blended_strength


def _ratings():
    codes = [t["code"] for t in seed_data.TEAMS]
    return fit_ratings(seed_data.synth_history(), codes)


def _str_by_code(ratings=None):
    """Build a minimal str_by_code using seed outright odds as market anchor."""
    market_dec = {t["code"]: t["dec"] for t in seed_data.TEAMS}
    codes = list(market_dec.keys())
    model_net = {}
    if ratings is not None:
        model_net = {
            c: ratings.teams[c].attack - ratings.teams[c].defense
            for c in codes
            if c in ratings.teams
        }
    n_matches = {c: 10 for c in codes}  # moderate data
    return blended_strength(model_net, market_dec, n_matches, codes)


def test_price_match_has_markets_and_ev():
    r = _ratings()
    s = _str_by_code(r)
    snap = price_match(
        "m1", "ESP", "CRO", r,
        market_odds={"home": 1.62, "draw": 4.0, "away": 5.8},
        str_by_code=s,
    )
    assert "1x2" in snap["markets"]
    # best may be None if no leg passes value filters, but key must exist
    assert "best" in snap
    if snap["best"] is not None:
        assert "ev" in snap["best"]


def test_price_match_legs_have_value_fields():
    """Each leg should carry value_score and is_value flag."""
    r = _ratings()
    s = _str_by_code(r)
    snap = price_match(
        "m1", "ESP", "CRO", r,
        market_odds={"home": 1.62, "draw": 4.0, "away": 5.8},
        str_by_code=s,
    )
    for leg in snap["legs"]:
        assert "value_score" in leg
        assert "is_value" in leg


def test_price_match_has_stage():
    """price_match should include stage in the returned dict."""
    r = _ratings()
    s = _str_by_code(r)
    snap = price_match(
        "m1", "ESP", "CRO", r,
        market_odds={"home": 1.62, "draw": 4.0, "away": 5.8},
        str_by_code=s,
        stage="group",
    )
    assert snap["stage"] == "group"

    snap_ko = price_match(
        "ko1", "ESP", "BRA", r,
        market_odds={"home": 1.90, "draw": 3.4, "away": 4.0},
        str_by_code=s,
        stage="knockout",
    )
    assert snap_ko["stage"] == "knockout"


def test_price_match_best_uses_value_score():
    """best leg must be highest value_score among legs passing the value-pick filter."""
    r = _ratings()
    s = _str_by_code(r)
    # ESP heavy favorite with tight home odds (home passes filter)
    snap = price_match(
        "test_vs", "ESP", "QAT", r,
        market_odds={"home": 1.30, "draw": 4.5, "away": 9.0},
        str_by_code=s,
    )
    value_legs = [leg for leg in snap["legs"] if leg["is_value"]]
    if snap["best"] is not None:
        # best must be the highest value_score among value legs
        best_vs = snap["best"]["value_score"]
        assert all(best_vs >= leg["value_score"] for leg in value_legs), (
            "best is not the highest value_score value leg"
        )


def test_price_match_longshot_not_best():
    """A longshot leg (dec >= 4.0 or p < 0.33) must NOT be selected as best."""
    r = _ratings()
    s = _str_by_code(r)
    snap = price_match(
        "test_ls", "ESP", "QAT", r,
        # home at 1.30 (tight favourite), away at 9.0 (longshot)
        market_odds={"home": 1.30, "draw": 4.5, "away": 9.0},
        str_by_code=s,
    )
    if snap["best"] is not None:
        assert snap["best"]["kind"] != "away", (
            f"Longshot 'away' at dec=9.0 should never be best; got {snap['best']}"
        )
        assert snap["best"]["dec"] <= 4.0, (
            f"best dec={snap['best']['dec']} exceeds max_dec=4.0 (longshot selected)"
        )
        assert snap["best"]["model"] >= 0.33, (
            f"best model prob {snap['best']['model']:.3f} < 0.33 (low-prob selected)"
        )


def test_price_match_stronger_home_favoured():
    """A much stronger home team should have home 1x2 prob > away prob."""
    r = _ratings()
    # ESP (str ~90) vs QAT (str ~52) — ESP as home should be heavy favourite
    s = _str_by_code(r)
    snap = price_match(
        "test_str", "ESP", "QAT", r,
        market_odds={"home": 1.30, "draw": 4.5, "away": 9.0},
        str_by_code=s,
    )
    legs = {leg["kind"]: leg for leg in snap["legs"]}
    assert legs["home"]["model"] > legs["away"]["model"], (
        f"Expected home prob > away prob; got home={legs['home']['model']:.3f}, "
        f"away={legs['away']['model']:.3f}"
    )


def test_price_outright_edge_signed():
    r = _ratings()
    s = _str_by_code(r)
    # champion_probs: ARG is favoured in this mini-tournament
    champion_probs = {"ARG": 0.25, "NGA": 0.02}
    rows = price_outright(champion_probs, {"ARG": 8.0, "NGA": 91.0}, s)
    arg = next(x for x in rows if x["code"] == "ARG")
    assert "edge" in arg and "ev" in arg and "kelly" in arg


def test_price_outright_model_equals_champion_probs():
    """price_outright must use the passed-in champion_probs directly as model."""
    r = _ratings()
    s = _str_by_code(r)
    champion_probs = {"ARG": 0.18, "NGA": 0.03, "ESP": 0.22}
    dec_by_code = {"ARG": 8.0, "NGA": 91.0, "ESP": 5.5}
    rows = price_outright(champion_probs, dec_by_code, s)
    by_code = {row["code"]: row for row in rows}
    for code, expected_model in champion_probs.items():
        assert by_code[code]["model"] == expected_model, (
            f"{code}: expected model={expected_model}, got {by_code[code]['model']}"
        )


def test_price_outright_str_from_str_by_code():
    """price_outright must use str_by_code for the str field, not ratings.str_rating."""
    r = _ratings()
    s = _str_by_code(r)
    champion_probs = {"ESP": 0.20, "QAT": 0.001}
    dec_by_code = {"ESP": 5.5, "QAT": 751.0}
    rows = price_outright(champion_probs, dec_by_code, s)
    by_code = {row["code"]: row for row in rows}
    # str field should match str_by_code
    assert abs(by_code["ESP"]["str"] - s["ESP"]) < 0.01
    assert abs(by_code["QAT"]["str"] - s["QAT"]) < 0.01
