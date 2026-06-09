import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
import app.db.models  # noqa: F401  (register tables)

@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    s = TestingSession()
    try:
        yield s
    finally:
        s.close()

@pytest.fixture()
def client(db_session):
    from app.main import app
    from app.db.session import get_db
    from fastapi.testclient import TestClient
    app.dependency_overrides[get_db] = lambda: iter([db_session])
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
