from app.providers.factory import get_football_provider, get_odds_provider, get_news_provider
from app.providers.seed.seed_football import SeedFootballProvider


def test_factory_falls_back_to_seed_without_keys(monkeypatch):
    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setenv("API_FOOTBALL_KEY", "")
    monkeypatch.setenv("ODDS_API_KEY", "")
    assert isinstance(get_football_provider(), SeedFootballProvider)
    assert get_odds_provider() is not None
    assert get_news_provider() is not None
