from __future__ import annotations
from fastapi import APIRouter
from app.models.betting import RISK

router = APIRouter()


@router.get("/meta")
def get_meta():
    return {
        "risk": RISK,
        "odds_formats": ["decimal", "american", "fractional"],
    }
