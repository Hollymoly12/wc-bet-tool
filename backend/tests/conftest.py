import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
import app.db.models  # noqa: F401  (register tables)


@pytest.fixture(autouse=True)
def _hermetic_seed_mode(monkeypatch):
    """Force seed mode for every test so the provider factory never hits live APIs.

    pydantic-settings reads the developer's real `backend/.env`; once it holds real
    keys, the factory would return live adapters and tests would make network calls
    (with rate-limit throttles → a 20+ minute suite). Empty env vars override the
    .env file, forcing the seed fallback.
    """
    from app.config import get_settings
    monkeypatch.setenv("ODDS_API_KEY", "")
    monkeypatch.setenv("API_FOOTBALL_KEY", "")
    monkeypatch.setenv("WIKI_SQUADS_ENABLED", "0")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def db_session():
    # Use a named in-memory DB shared across all connections in the same process.
    # `?check_same_thread=false` allows cross-thread use.
    engine = create_engine(
        "sqlite:///file::memory:?cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    s = TestingSession()
    try:
        yield s
    finally:
        s.close()
        # Drop all tables so next test starts fresh
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    from app.main import app
    from app.db.session import get_db
    from fastapi.testclient import TestClient

    def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
