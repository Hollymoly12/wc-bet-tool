from app.providers.seed.seed_football import SeedFootballProvider
from app.providers.seed.seed_odds import SeedOddsProvider
from app.providers.seed.seed_news import SeedNewsProvider


def test_seed_football_fixtures_and_results():
    p = SeedFootballProvider()
    assert len(p.fetch_fixtures()) >= 8
    assert len(p.fetch_results()) > 50
    assert "ESP" in p.fetch_squads()


def test_seed_odds_lines_present():
    lines = SeedOddsProvider().fetch_odds()
    assert any(l.market_key.startswith("h2h:") for l in lines)


def test_seed_news_has_tags():
    items = SeedNewsProvider().fetch_news()
    assert {i.tag for i in items} & {"form", "injury", "intel", "lineup", "susp"}
