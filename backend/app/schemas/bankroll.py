from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class BetIn(BaseModel):
    key: str
    pick: str
    team: str = ""
    market: str = ""
    stake: float
    dec: float


class BetOut(BaseModel):
    id: int
    key: str
    pick: str
    team: str
    market: str
    stake: float
    dec: float
    status: str
    pnl: float
    placed_at: datetime


class SettleIn(BaseModel):
    result: str  # won | lost | void


class BankrollResponse(BaseModel):
    balance: float
    start: float
    currency: str = "€"
    open_bets: list[BetOut]
    settled_bets: list[BetOut]
