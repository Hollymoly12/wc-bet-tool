from __future__ import annotations
from fastapi import APIRouter
from app.api.deps import DbDep
from app.db.models import TeamNews

router = APIRouter()


@router.get("/news/{code}")
def get_news(code: str, db: DbDep):
    news = db.query(TeamNews).filter(TeamNews.code == code).all()
    return [
        {
            "tag": n.tag,
            "text": n.text,
            "source": n.source,
            "url": n.url,
            "published_at": n.published_at.isoformat() if n.published_at else None,
        }
        for n in news
    ]
