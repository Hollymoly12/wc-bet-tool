import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
import app.db.models  # noqa: F401  (register tables)


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
