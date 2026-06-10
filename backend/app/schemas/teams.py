from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class TeamSummary(BaseModel):
    code: str
    name: str
    group: str
    str: float
    form: str
    elo: float


class PlayerEntry(BaseModel):
    id: int
    code: str
    number: int
    name: str
    pos: str
    club: str
    tier: float
    starter: bool


class TeamDetail(TeamSummary):
    colors: list[str]
    attack: float
    defense: float
    squad: list[PlayerEntry]
    outright: dict | None = None
    news: list[dict]
