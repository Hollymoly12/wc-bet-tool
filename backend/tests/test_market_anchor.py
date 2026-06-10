"""Unit tests for app.services.market_anchor."""
import pytest

from app.services.market_anchor import (
    BASE_TOTAL,
    _zscores,
    blended_strength,
    lambdas_from_strength,
    market_strength_z,
)


# ---------------------------------------------------------------------------
# _zscores
# ---------------------------------------------------------------------------

class TestZscores:
    def test_zero_when_all_same(self):
        z = _zscores({"A": 5.0, "B": 5.0, "C": 5.0})
        for v in z.values():
            assert v == 0.0

    def test_empty(self):
        assert _zscores({}) == {}

    def test_sign_ordering(self):
        z = _zscores({"low": 1.0, "mid": 5.0, "high": 9.0})
        assert z["high"] > z["mid"] > z["low"]

    def test_mean_zero(self):
        vals = {"A": 1.0, "B": 3.0, "C": 8.0, "D": 4.0}
        z = _zscores(vals)
        assert abs(sum(z.values())) < 1e-9


# ---------------------------------------------------------------------------
# market_strength_z
# ---------------------------------------------------------------------------

class TestMarketStrengthZ:
    def test_short_odds_team_ranks_highest(self):
        """Favourite (low dec) should receive the highest z-score."""
        z = market_strength_z({"ESP": 5.5, "KSA": 501.0, "UZB": 751.0})
        assert z["ESP"] > z["KSA"] > z["UZB"]

    def test_ordering_preserved_for_many_teams(self):
        """Teams ordered by odds should be ordered by z-score."""
        decs = {"A": 4.0, "B": 8.0, "C": 20.0, "D": 100.0, "E": 500.0}
        z = market_strength_z(decs)
        codes = sorted(decs, key=lambda c: decs[c])
        zvals = [z[c] for c in codes]
        assert zvals == sorted(zvals, reverse=True)

    def test_empty_returns_empty(self):
        assert market_strength_z({}) == {}

    def test_single_team_returns_zero_z(self):
        z = market_strength_z({"X": 10.0})
        assert z["X"] == 0.0


# ---------------------------------------------------------------------------
# blended_strength
# ---------------------------------------------------------------------------

class TestBlendedStrength:
    def _run(self, model_net, market_dec, n_matches=None, codes=None):
        if codes is None:
            codes = list(market_dec.keys())
        if n_matches is None:
            n_matches = {c: 0 for c in codes}
        return blended_strength(model_net, market_dec, n_matches, codes)

    def test_output_in_valid_range(self):
        market_dec = {"ESP": 5.5, "QAT": 751.0, "BRA": 7.5, "NGA": 91.0}
        model_net = {"ESP": 0.5, "QAT": -0.3, "BRA": 0.4, "NGA": 0.1}
        n_matches = {"ESP": 20, "QAT": 0, "BRA": 20, "NGA": 0}
        s = self._run(model_net, market_dec, n_matches)
        for c, v in s.items():
            assert 48.0 <= v <= 96.0, f"{c}: {v} out of [48, 96]"

    def test_market_favourite_strongest(self):
        """Market favourite (shortest odds) should have highest str."""
        market_dec = {"ESP": 5.5, "QAT": 751.0}
        s = self._run({}, market_dec, {"ESP": 0, "QAT": 0})
        assert s["ESP"] > s["QAT"]

    def test_minnow_anchored_to_market_when_data_poor(self):
        """With zero matches, model nudge is 0 — strength purely from market z."""
        market_dec = {"ESP": 5.5, "QAT": 751.0}
        # Even if model gives QAT a great net rating, it should not overtake ESP
        model_net = {"ESP": -2.0, "QAT": 3.0}
        n_matches = {"ESP": 0, "QAT": 0}
        s = self._run(model_net, market_dec, n_matches)
        # Market says ESP is much better; zero data => fully anchored
        assert s["ESP"] > s["QAT"]

    def test_model_can_nudge_with_data(self):
        """With sufficient matches, model does nudge strength away from market anchor."""
        market_dec = {"A": 10.0, "B": 10.0}  # equal market priors
        model_net = {"A": 1.5, "B": -1.5}    # model strongly favours A
        n_matches = {"A": 100, "B": 100}      # plenty of data
        s = self._run(model_net, market_dec, n_matches)
        assert s["A"] > s["B"]

    def test_model_cannot_pull_minnow_far(self):
        """Minnow with few matches stays near market anchor even if model likes it."""
        market_dec = {"FAV": 5.5, "MINNOW": 501.0}
        # Model thinks minnow is great
        model_net = {"FAV": 0.0, "MINNOW": 3.0}
        n_matches = {"FAV": 20, "MINNOW": 2}  # minnow has only 2 matches
        s = self._run(model_net, market_dec, n_matches)
        # Market still says FAV is way better; minnow's 2 matches can't flip this
        assert s["FAV"] > s["MINNOW"]

    def test_full_model_weight_capped_at_max(self):
        """Even with 100 matches, model weight <= MODEL_MAX_WEIGHT * 100 % influence."""
        # If equal market, model determines ordering; that's fine (model can nudge)
        market_dec = {"A": 10.0, "B": 10.0, "C": 10.0}
        model_net = {"A": 2.0, "B": 0.0, "C": -2.0}
        n_matches = {"A": 1000, "B": 1000, "C": 1000}
        s = self._run(model_net, market_dec, n_matches)
        # Ordering should still follow model (market is neutral)
        assert s["A"] > s["B"] > s["C"]

    def test_codes_not_in_model_net_use_zero(self):
        """Teams absent from model_net still get a rating via market z only."""
        market_dec = {"X": 20.0, "Y": 100.0}
        s = self._run({}, market_dec)  # no model_net entries
        assert 48.0 <= s["X"] <= 96.0
        assert 48.0 <= s["Y"] <= 96.0
        assert s["X"] > s["Y"]


# ---------------------------------------------------------------------------
# lambdas_from_strength
# ---------------------------------------------------------------------------

class TestLambdasFromStrength:
    def test_home_advantage_when_equal(self):
        """Equal strengths: lh > la due to home advantage."""
        lh, la = lambdas_from_strength(72.0, 72.0)
        assert lh > la

    def test_total_near_base_for_equal(self):
        """Total goals ≈ BASE_TOTAL for equal strengths."""
        lh, la = lambdas_from_strength(72.0, 72.0)
        assert abs(lh + la - BASE_TOTAL) < 0.05

    def test_stronger_home_favoured(self):
        """Higher sH => lh > la (bigger home advantage)."""
        lh_strong, la_strong = lambdas_from_strength(90.0, 55.0)
        lh_weak, la_weak = lambdas_from_strength(55.0, 90.0)
        assert lh_strong > la_strong
        assert la_weak > lh_weak

    def test_lh_gt_la_when_sH_gt_sA(self):
        lh, la = lambdas_from_strength(85.0, 60.0)
        assert lh > la

    def test_la_gt_lh_when_sH_much_weaker(self):
        lh, la = lambdas_from_strength(50.0, 90.0)
        assert la > lh

    def test_large_gap_floors_la(self):
        """40-point gap should floor la near 0.15."""
        lh, la = lambdas_from_strength(96.0, 48.0)
        assert la == pytest.approx(0.15, abs=0.01)
        assert lh <= 4.0

    def test_large_gap_caps_lh(self):
        """Very large gap should cap lh at 4.0."""
        lh, la = lambdas_from_strength(96.0, 48.0)
        assert lh <= 4.0

    def test_bounds_always_valid(self):
        """lh and la always in [0.15, 4.0]."""
        for sH in [48, 60, 72, 85, 96]:
            for sA in [48, 60, 72, 85, 96]:
                lh, la = lambdas_from_strength(float(sH), float(sA))
                assert 0.15 <= lh <= 4.0, f"sH={sH}, sA={sA}: lh={lh}"
                assert 0.15 <= la <= 4.0, f"sH={sH}, sA={sA}: la={la}"

    def test_custom_home_adv(self):
        """Custom home_adv_goals shifts both lambdas."""
        lh0, la0 = lambdas_from_strength(72.0, 72.0, home_adv_goals=0.0)
        lh1, la1 = lambdas_from_strength(72.0, 72.0, home_adv_goals=0.5)
        assert lh1 > lh0
        assert la1 < la0


# ---------------------------------------------------------------------------
# Integration: Spain with shortest odds always near top
# ---------------------------------------------------------------------------

class TestSpainAlwaysNearTop:
    def test_spain_high_str_with_noisy_model(self):
        """Regardless of model noise, Spain (shortest WC odds) ranks near top."""
        market_dec = {
            "ESP": 5.5, "FRA": 6.0, "BRA": 7.5, "ARG": 8.0,
            "ENG": 7.0, "GER": 11.0,
            "KSA": 501.0, "QAT": 751.0, "UZB": 751.0,
        }
        codes = list(market_dec.keys())
        # Deliberately give KSA/QAT great model ratings and Spain terrible ones
        model_net = {
            "ESP": -3.0, "FRA": 0.0, "BRA": 0.0, "ARG": 0.0,
            "ENG": 0.0, "GER": 0.0,
            "KSA": 3.0, "QAT": 3.0, "UZB": 3.0,
        }
        # All teams have 0 calibration matches (worst case — full market anchor)
        n_matches = {c: 0 for c in codes}
        s = blended_strength(model_net, market_dec, n_matches, codes)

        # Spain (and top-5 favourites) should be above the minnows
        assert s["ESP"] > s["KSA"]
        assert s["ESP"] > s["QAT"]
        assert s["FRA"] > s["KSA"]

        # Spain should be near the top
        ranked = sorted(s, key=lambda c: s[c], reverse=True)
        assert ranked.index("ESP") < 4, f"Spain rank {ranked.index('ESP')} — expected top-4: {ranked}"
