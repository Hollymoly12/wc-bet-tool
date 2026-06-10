from __future__ import annotations
from pydantic import BaseModel


class MetaResponse(BaseModel):
    risk: dict
    odds_formats: list[str]
