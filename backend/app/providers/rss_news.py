"""RSS news adapter — scrapes football news feeds and emits NewsItem DTOs.

Feeds are parsed with feedparser (no network in tests — monkeypatch feedparser.parse).
For each entry whose title/summary contains a known WC team name, we emit a
NewsItem tagged 'form' (if the text contains form-related keywords) or 'intel'.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from app.providers.base import NewsItem
from app.seed import seed_data

logger = logging.getLogger(__name__)

# Default RSS feed list — publicly available football RSS endpoints
FEEDS: list[str] = [
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.espn.com/espn/rss/soccer/news",
    "https://www.skysports.com/rss/12040",      # Sky Sports football
    "https://www.cbssports.com/rss/headlines/soccer/",
]

# Form-related keywords that push an item into the 'form' category
_FORM_KEYWORDS = {
    "form", "streak", "unbeaten", "wins", "winning", "lost", "loss",
    "defeat", "clean sheet", "scoreless", "result",
}

# Build a lowercase name → code reverse map once at module load
_NAME_TO_CODE: dict[str, str] = {
    name.lower(): code for code, name in seed_data.NAMES.items()
}


def _tag_for_text(text: str) -> str:
    lower = text.lower()
    if any(kw in lower for kw in _FORM_KEYWORDS):
        return "form"
    return "intel"


def _match_team(title: str, summary: str) -> str | None:
    """Return the first team code found in title+summary, or None."""
    combined = (title + " " + summary).lower()
    for name, code in _NAME_TO_CODE.items():
        if name in combined:
            return code
    return None


def _parse_published(entry) -> datetime:
    """Try to parse the entry published date; fall back to now(utc)."""
    try:
        raw = getattr(entry, "published", None) or getattr(entry, "updated", None)
        if raw:
            return parsedate_to_datetime(raw).astimezone(timezone.utc)
    except Exception:
        pass
    return datetime.now(timezone.utc)


class RssNewsAdapter:
    """Parses a list of RSS feeds and emits NewsItems for WC team mentions."""

    def __init__(self, feeds: list[str] | None = None) -> None:
        self._feeds = feeds if feeds is not None else FEEDS

    def fetch_news(self) -> list[NewsItem]:
        out: list[NewsItem] = []
        for feed_url in self._feeds:
            try:
                parsed = feedparser.parse(feed_url)
            except Exception as exc:
                logger.warning("RssNewsAdapter: failed to parse %r — %s", feed_url, exc)
                continue

            feed_obj = parsed.feed if parsed.feed else None
            if feed_obj is not None:
                # feedparser.FeedParserDict supports .get(); SimpleNamespace uses getattr
                try:
                    feed_title = feed_obj.get("title", feed_url)
                except AttributeError:
                    feed_title = getattr(feed_obj, "title", feed_url)
            else:
                feed_title = feed_url

            # feedparser returns dict-like FeedParserDict; tests use SimpleNamespace
            try:
                entries = parsed.get("entries", [])
            except AttributeError:
                entries = getattr(parsed, "entries", [])

            for entry in entries:
                try:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")
                    link = entry.get("link", "")
                except AttributeError:
                    title = getattr(entry, "title", "")
                    summary = getattr(entry, "summary", "")
                    link = getattr(entry, "link", "")

                code = _match_team(title, summary)
                if code is None:
                    continue

                tag = _tag_for_text(title + " " + summary)
                pub = _parse_published(entry)

                out.append(NewsItem(
                    code=code,
                    tag=tag,
                    text=title,
                    source=feed_title,
                    url=link,
                    published_at=pub,
                ))

        return out
