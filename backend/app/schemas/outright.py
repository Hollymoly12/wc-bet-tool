from __future__ import annotations
from pydantic import BaseModel


class OuTrirightRow(BaseModel):
    code: str
    name: str
    group: str
    colors: list[str]
    dec: float
    model: float
    implied: float
    fair: float
    edge: float
    ev: float
    kelly: float
    verdict: str
    str: float
