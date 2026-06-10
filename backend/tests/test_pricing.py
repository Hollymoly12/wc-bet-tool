from app.services.pricing import price_match, price_outright
from app.models.ratings import fit_ratings
from app.seed import seed_data


def _ratings():
    codes = [t["code"] for t in seed_data.TEAMS]
    return fit_ratings(seed_data.synth_history(), codes)


def test_price_match_has_markets_and_ev():
    r = _ratings()
    snap = price_match("m1", "ESP", "CRO", r,
                       market_odds={"home": 1.62, "draw": 4.0, "away": 5.8})
    assert "1x2" in snap["markets"]
    assert "best" in snap and "ev" in snap["best"]


def test_price_outright_edge_signed():
    r = _ratings()
    rows = price_outright(r, {"ARG": 8.0, "NGA": 91.0})
    arg = next(x for x in rows if x["code"] == "ARG")
    assert "edge" in arg and "ev" in arg and "kelly" in arg
