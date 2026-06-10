"""Composite NewsProvider — merges several news sources, tolerating per-source failures.

Used in real mode to combine structured injury/suspension data (API-Football) with
free-text headlines (RSS). If one source raises (network, parse), it is skipped so the
others still return.
"""
from __future__ import annotations

import logging

from app.providers.base import NewsItem

logger = logging.getLogger(__name__)


class CompositeNewsProvider:
    def __init__(self, providers: list) -> None:
        self._providers = providers

    def fetch_news(self) -> list[NewsItem]:
        items: list[NewsItem] = []
        for p in self._providers:
            try:
                items.extend(p.fetch_news())
            except Exception as exc:  # noqa: BLE001 - one bad source must not sink the rest
                logger.warning("news source %s failed: %s", type(p).__name__, exc)
        return items
