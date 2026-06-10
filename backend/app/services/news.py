"""News refresh service — fetches news items via provider and persists to team_news."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import TeamNews
from app.providers.base import NewsItem


def refresh_news(db: Session, items: list[NewsItem]) -> int:
    """Persist news items to team_news table. Returns count inserted."""
    now = datetime.now(timezone.utc)
    count = 0
    for item in items:
        row = TeamNews(
            code=item.code,
            tag=item.tag,
            text=item.text,
            source=item.source,
            url=item.url,
            published_at=item.published_at,
        )
        db.add(row)
        count += 1
    db.commit()
    return count
