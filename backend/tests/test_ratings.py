# backend/tests/test_ratings.py
from app.models.ratings import fit_ratings, TeamRatings


def _history():
    # ARG (strong) beats NGA (weak) repeatedly at home and away
    h = []
    for _ in range(15):
        h.append({"home": "ARG", "away": "NGA", "home_goals": 3, "away_goals": 0, "days_ago": 100})
        h.append({"home": "NGA", "away": "ARG", "home_goals": 0, "away_goals": 2, "days_ago": 100})
    return h


def test_fit_returns_ratings_per_team():
    r = fit_ratings(_history(), codes=["ARG", "NGA"], halflife_days=540)
    assert set(r.teams) == {"ARG", "NGA"}
    assert isinstance(r.teams["ARG"], TeamRatings)


def test_stronger_team_has_higher_net_rating():
    r = fit_ratings(_history(), codes=["ARG", "NGA"], halflife_days=540)
    arg = r.teams["ARG"]; nga = r.teams["NGA"]
    # net = attack - defense ; ARG should dominate
    assert (arg.attack - arg.defense) > (nga.attack - nga.defense)


def test_home_advantage_positive():
    r = fit_ratings(_history(), codes=["ARG", "NGA"], halflife_days=540)
    assert r.home_adv > 0


def test_ratings_fits_full_seed():
    """Smoke test: 48-team fit on synth_history must complete without error."""
    from app.seed import seed_data
    codes = [t["code"] for t in seed_data.TEAMS]
    history = seed_data.synth_history()
    r = fit_ratings(history, codes=codes)
    assert len(r.teams) == 48
    for c in codes:
        assert isinstance(r.teams[c], TeamRatings)
