from __future__ import annotations
from fastapi import APIRouter
from app.api.deps import DbDep
from app.services.ingestion import run_refresh

router = APIRouter()


@router.post("/admin/refresh")
def admin_refresh(db: DbDep):
    run_refresh(db, sims=20000)
    return {"status": "ok"}
