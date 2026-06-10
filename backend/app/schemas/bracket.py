from __future__ import annotations
from pydantic import BaseModel


class BracketTeam(BaseModel):
    code: str
    name: str
    str: float
    winProb: float | None = None


class BracketMatch(BaseModel):
    a: BracketTeam | None = None
    b: BracketTeam | None = None
    winner: BracketTeam | None = None


class BracketRound(BaseModel):
    name: str
    matches: list[BracketMatch]


class BracketResponse(BaseModel):
    rounds: list[BracketRound]
    champion: BracketTeam | None = None
