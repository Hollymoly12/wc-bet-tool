from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class MatchLeg(BaseModel):
    kind: str
    dec: float
    model: float
    implied: float
    fair: float
    edge: float
    ev: float
    kelly: float
    verdict: str


class MatchSummary(BaseModel):
    id: str
    home: str
    away: str
    homeName: str
    awayName: str
    group: str
    day: str
    time: str
    venue: str
    xg: list[float]
    conf: int
    best: MatchLeg | None = None
    kickoff: str | None = None


class MatchDetail(MatchSummary):
    markets: dict[str, Any]
    legs: list[MatchLeg]
    h2h: list[dict]
