from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class NewsItem(BaseModel):
    tag: str
    text: str
    source: str
    url: str
    published_at: datetime
