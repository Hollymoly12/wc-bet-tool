"""CLI entry point for the WC bet tool backend.

Usage:
    python -m app.cli refresh       # run full data refresh (real DB via SessionLocal)
    python -m app.cli init-db       # create all tables (Base.metadata.create_all)
"""
from __future__ import annotations
import argparse


def cmd_refresh(args) -> None:
    from app.db.session import SessionLocal
    from app.services.ingestion import run_refresh
    sims = getattr(args, "sims", 50000)
    print(f"Running refresh (sims={sims})...")
    db = SessionLocal()
    try:
        run_refresh(db, sims=sims)
        print("Refresh complete.")
    finally:
        db.close()


def cmd_init_db(args) -> None:
    from app.db.session import engine
    from app.db.base import Base
    import app.db.models  # noqa: F401 — register all ORM tables
    print("Creating all tables...")
    Base.metadata.create_all(engine)
    print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="WC Bet Tool CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_refresh = sub.add_parser("refresh", help="Run the full data + model refresh pipeline")
    p_refresh.add_argument("--sims", type=int, default=50000,
                           help="Monte-Carlo simulation count (default: 50000)")
    p_refresh.set_defaults(func=cmd_refresh)

    p_init = sub.add_parser("init-db", help="Create all DB tables (idempotent)")
    p_init.set_defaults(func=cmd_init_db)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
