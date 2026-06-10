"""CLI entry point for the WC bet tool backend.

Usage:
    python -m app.cli refresh       # run full data refresh (real DB via SessionLocal)
    python -m app.cli init-db       # create all tables (Base.metadata.create_all)

DATABASE_URL is read from the environment (or .env file via pydantic-settings).
In production set DATABASE_URL=postgresql+psycopg://... before running.
"""
from __future__ import annotations
import argparse
import sys
import time


_MAX_RETRIES = 3
_RETRY_DELAY = 15  # seconds between retries


def cmd_refresh(args) -> None:
    from app.db.session import SessionLocal
    from app.services.ingestion import run_refresh
    sims = getattr(args, "sims", 50000)
    print(f"Running refresh (sims={sims})...")

    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        db = SessionLocal()
        try:
            run_refresh(db, sims=sims)
            print("Refresh complete.")
            return
        except Exception as exc:
            last_exc = exc
            print(f"[attempt {attempt}/{_MAX_RETRIES}] Refresh failed: {exc}", file=sys.stderr)
            if attempt < _MAX_RETRIES:
                print(f"Retrying in {_RETRY_DELAY}s...", file=sys.stderr)
                time.sleep(_RETRY_DELAY)
        finally:
            db.close()

    print(f"Refresh failed after {_MAX_RETRIES} attempts. Last error: {last_exc}", file=sys.stderr)
    sys.exit(1)


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
