from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class PlayerListItem(BaseModel):
    id: int
    name: str
    pos: str
    number: int


class PlayerDetail(BaseModel):
    id: int
    code: str
    team: str
    number: int
    name: str
    pos: str
    club: str
    tier: float
    starter: bool
    props: dict[str, Any]
