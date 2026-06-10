from __future__ import annotations
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import ModelSnapshot, TournamentSnapshot

DbDep = Annotated[Session, Depends(get_db)]


def latest_snapshot(db: Session, kind: str, ref: str | None = None) -> ModelSnapshot | None:
    """Return the most recent ModelSnapshot for the given kind and optional ref."""
    q = db.query(ModelSnapshot).filter(ModelSnapshot.kind == kind)
    if ref is not None:
        q = q.filter(ModelSnapshot.ref == ref)
    return q.order_by(ModelSnapshot.created_at.desc()).first()


def latest_tournament_snapshot(db: Session) -> TournamentSnapshot | None:
    return db.query(TournamentSnapshot).order_by(TournamentSnapshot.created_at.desc()).first()
