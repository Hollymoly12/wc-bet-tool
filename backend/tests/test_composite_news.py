from datetime import datetime, timezone

from app.providers.base import NewsItem
from app.providers.composite_news import CompositeNewsProvider


def _item(code, tag, text):
    return NewsItem(code=code, tag=tag, text=text, source="t", url="",
                    published_at=datetime.now(timezone.utc))


class _Good:
    def __init__(self, items):
        self._items = items

    def fetch_news(self):
        return self._items


class _Boom:
    def fetch_news(self):
        raise RuntimeError("network down")


def test_composite_merges_sources():
    c = CompositeNewsProvider([_Good([_item("ESP", "injury", "a")]),
                               _Good([_item("FRA", "form", "b")])])
    items = c.fetch_news()
    assert {i.code for i in items} == {"ESP", "FRA"}


def test_composite_tolerates_failing_source():
    c = CompositeNewsProvider([_Boom(), _Good([_item("ESP", "intel", "x")])])
    items = c.fetch_news()
    assert [i.code for i in items] == ["ESP"]
