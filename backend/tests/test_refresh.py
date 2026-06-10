from app.services.ingestion import run_refresh
from app.db.models import ModelSnapshot, TournamentSnapshot, Team


def test_refresh_populates_snapshots(db_session):
    run_refresh(db_session, sims=500)
    assert db_session.query(Team).count() == 48
    assert db_session.query(ModelSnapshot).filter_by(kind="match").count() >= 8
    assert db_session.query(ModelSnapshot).filter_by(kind="outright").count() >= 1
    assert db_session.query(TournamentSnapshot).count() == 1
