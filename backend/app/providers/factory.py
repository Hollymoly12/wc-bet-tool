"""Env-based provider factory — selects real adapters when keys present, seed fallback otherwise.

IMPORTANT: Each factory function calls get_settings() fresh so that monkeypatched
env vars in tests are honored (get_settings() has lru_cache, so callers must call
get_settings.cache_clear() before patching env for the change to take effect).
"""
from __future__ import annotations
from app.config import get_settings
from app.providers.seed.seed_football import SeedFootballProvider
from app.providers.seed.seed_odds import SeedOddsProvider
from app.providers.seed.seed_news import SeedNewsProvider


def get_football_provider():
    s = get_settings()
    if s.has_football_key:
        from app.providers.api_football import ApiFootballAdapter
        return ApiFootballAdapter()
    return SeedFootballProvider()


def get_odds_provider():
    s = get_settings()
    if s.has_odds_key:
        from app.providers.the_odds_api import TheOddsApiAdapter
        return TheOddsApiAdapter()
    return SeedOddsProvider()


def get_news_provider():
    s = get_settings()
    if s.has_football_key:
        # Real mode: structured injuries/suspensions (API-Football) + RSS headlines.
        from app.providers.composite_news import CompositeNewsProvider
        from app.providers.injuries import InjuriesNewsProvider
        from app.providers.rss_news import RssNewsAdapter
        return CompositeNewsProvider([InjuriesNewsProvider(), RssNewsAdapter()])
    return SeedNewsProvider()
