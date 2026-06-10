"""Tests for RssNewsAdapter.

feedparser.parse is monkeypatched to return fake parsed objects so no real
network calls are made.
"""
from __future__ import annotations

from types import SimpleNamespace


from app.providers.rss_news import RssNewsAdapter

# ---------------------------------------------------------------------------
# Fake feedparser result helpers
# ---------------------------------------------------------------------------

def _make_entry(title: str, summary: str = "", link: str = "https://example.com/article",
                published: str = "Mon, 10 Jun 2026 12:00:00 +0000"):
    return SimpleNamespace(
        title=title,
        summary=summary,
        link=link,
        published=published,
    )


def _make_parsed(feed_title: str, entries):
    return SimpleNamespace(
        feed=SimpleNamespace(title=feed_title),
        entries=entries,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_single_entry_matched(monkeypatch):
    """An entry mentioning 'Spain' should produce one NewsItem with code=ESP."""
    fake = _make_parsed("Test Feed", [
        _make_entry("Spain dominate warm-up match with 4-0 win"),
    ])
    monkeypatch.setattr("feedparser.parse", lambda url: fake)

    adapter = RssNewsAdapter(feeds=["https://fake.example.com/rss"])
    items = adapter.fetch_news()
    assert len(items) == 1
    assert items[0].code == "ESP"


def test_no_team_mention_skipped(monkeypatch):
    """An entry with no known team name produces no output."""
    fake = _make_parsed("Test Feed", [
        _make_entry("Transfer rumours at unknown club swirl"),
    ])
    monkeypatch.setattr("feedparser.parse", lambda url: fake)

    adapter = RssNewsAdapter(feeds=["https://fake.example.com/rss"])
    assert adapter.fetch_news() == []


def test_form_tag(monkeypatch):
    """Entries with form-related keywords should get tag='form'."""
    fake = _make_parsed("Test Feed", [
        _make_entry("France on a winning streak ahead of opener"),
    ])
    monkeypatch.setattr("feedparser.parse", lambda url: fake)

    adapter = RssNewsAdapter(feeds=["https://fake.example.com/rss"])
    items = adapter.fetch_news()
    assert len(items) == 1
    assert items[0].tag == "form"
    assert items[0].code == "FRA"


def test_intel_tag(monkeypatch):
    """Generic entries without form keywords should get tag='intel'."""
    fake = _make_parsed("Test Feed", [
        _make_entry("Brazil tactical preview: compact defence expected"),
    ])
    monkeypatch.setattr("feedparser.parse", lambda url: fake)

    adapter = RssNewsAdapter(feeds=["https://fake.example.com/rss"])
    items = adapter.fetch_news()
    assert len(items) == 1
    assert items[0].tag == "intel"
    assert items[0].code == "BRA"


def test_source_from_feed_title(monkeypatch):
    """NewsItem.source should equal the feed title."""
    fake = _make_parsed("BBC Sport", [
        _make_entry("Germany set for key selection"),
    ])
    monkeypatch.setattr("feedparser.parse", lambda url: fake)

    adapter = RssNewsAdapter(feeds=["https://fake.example.com/rss"])
    items = adapter.fetch_news()
    assert items[0].source == "BBC Sport"


def test_url_carried_through(monkeypatch):
    """NewsItem.url should carry the entry link."""
    fake = _make_parsed("ESPN", [
        _make_entry("Portugal injury update", link="https://espn.com/wc/portugal"),
    ])
    monkeypatch.setattr("feedparser.parse", lambda url: fake)

    adapter = RssNewsAdapter(feeds=["https://fake.example.com/rss"])
    items = adapter.fetch_news()
    assert items[0].url == "https://espn.com/wc/portugal"


def test_published_at_parsed(monkeypatch):
    """published_at should be a timezone-aware UTC datetime."""
    from datetime import timezone
    fake = _make_parsed("Feed", [
        _make_entry("Spain news", published="Mon, 10 Jun 2026 12:00:00 +0000"),
    ])
    monkeypatch.setattr("feedparser.parse", lambda url: fake)

    adapter = RssNewsAdapter(feeds=["https://fake.example.com/rss"])
    items = adapter.fetch_news()
    assert items[0].published_at.tzinfo is not None
    assert items[0].published_at.tzinfo == timezone.utc


def test_multiple_feeds(monkeypatch):
    """Items from multiple feeds are concatenated."""
    fake1 = _make_parsed("Feed 1", [_make_entry("Spain preview")])
    fake2 = _make_parsed("Feed 2", [_make_entry("France injury concern")])
    results = iter([fake1, fake2])
    monkeypatch.setattr("feedparser.parse", lambda url: next(results))

    adapter = RssNewsAdapter(feeds=["https://f1.com/rss", "https://f2.com/rss"])
    items = adapter.fetch_news()
    assert len(items) == 2
    codes = {i.code for i in items}
    assert "ESP" in codes
    assert "FRA" in codes


def test_empty_entries(monkeypatch):
    """Feed with no entries produces no items."""
    fake = _make_parsed("Empty Feed", [])
    monkeypatch.setattr("feedparser.parse", lambda url: fake)

    adapter = RssNewsAdapter(feeds=["https://empty.example.com/rss"])
    assert adapter.fetch_news() == []


def test_alias_team_resolution(monkeypatch):
    """'South Korea' (in NAMES) should resolve to KOR."""
    fake = _make_parsed("Test", [_make_entry("South Korea record big win")])
    monkeypatch.setattr("feedparser.parse", lambda url: fake)

    adapter = RssNewsAdapter(feeds=["https://fake.example.com/rss"])
    items = adapter.fetch_news()
    assert len(items) == 1
    assert items[0].code == "KOR"
