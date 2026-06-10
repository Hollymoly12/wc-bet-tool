from __future__ import annotations
from pydantic import BaseModel


class GroupMarket(BaseModel):
    dec: float
    implied: float
    model: float
    ev: float


class GroupRow(BaseModel):
    code: str
    name: str
    group: str
    str: float
    form: str
    gwProb: float
    qualProb: float
    thirdProb: float
    projRank: int
    gwMarket: GroupMarket
    qualMarket: GroupMarket


class GroupResponse(BaseModel):
    letter: str
    rows: list[GroupRow]
