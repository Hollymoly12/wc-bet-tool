"""Integration tests for the run_refresh pipeline in seed mode."""
from app.services.ingestion import run_refresh
from app.db.models import ModelSnapshot, TournamentSnapshot, Team


def test_refresh_populates_snapshots(db_session):
    run_refresh(db_session, sims=500)
    assert db_session.query(Team).count() == 48
    assert db_session.query(ModelSnapshot).filter_by(kind="match").count() >= 8
    assert db_session.query(ModelSnapshot).filter_by(kind="outright").count() >= 1
    assert db_session.query(TournamentSnapshot).count() == 1


def test_outright_model_probs_are_valid(db_session):
    """Each outright row's model probability must be in [0, 1]."""
    run_refresh(db_session, sims=500)
    snap = (
        db_session.query(ModelSnapshot)
        .filter_by(kind="outright")
        .order_by(ModelSnapshot.created_at.desc())
        .first()
    )
    assert snap is not None
    rows = snap.payload["rows"]
    for row in rows:
        assert 0.0 <= row["model"] <= 1.0, (
            f"{row['code']}: model={row['model']} not in [0, 1]"
        )


def test_outright_model_sum_near_one(db_session):
    """Sum of champion probs (model column) over all outright rows must ≈ 1."""
    run_refresh(db_session, sims=500)
    snap = (
        db_session.query(ModelSnapshot)
        .filter_by(kind="outright")
        .order_by(ModelSnapshot.created_at.desc())
        .first()
    )
    assert snap is not None
    total = sum(row["model"] for row in snap.payload["rows"])
    # With 500 sims, champion probs sum to exactly 1 by construction
    assert abs(total - 1.0) < 0.02, f"Sum of outright models = {total:.4f}, expected ≈ 1"


def test_no_minnow_wins_world_cup(db_session):
    """No single team should have a champion prob > 0.6 (sanity cap)."""
    run_refresh(db_session, sims=500)
    snap = (
        db_session.query(ModelSnapshot)
        .filter_by(kind="outright")
        .order_by(ModelSnapshot.created_at.desc())
        .first()
    )
    assert snap is not None
    for row in snap.payload["rows"]:
        assert row["model"] <= 0.6, (
            f"{row['code']}: model={row['model']:.3f} exceeds 0.6 — degenerate prediction"
        )


def test_outright_rows_have_required_fields(db_session):
    """Every outright row must carry all required schema fields."""
    run_refresh(db_session, sims=500)
    snap = (
        db_session.query(ModelSnapshot)
        .filter_by(kind="outright")
        .order_by(ModelSnapshot.created_at.desc())
        .first()
    )
    assert snap is not None
    required = {"code", "dec", "model", "implied", "fair", "edge", "ev", "kelly", "verdict", "str"}
    for row in snap.payload["rows"]:
        missing = required - set(row.keys())
        assert not missing, f"{row.get('code', '?')}: missing fields {missing}"
