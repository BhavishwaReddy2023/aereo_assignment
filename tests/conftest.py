import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.config import settings

# In-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create fresh database tables for each test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session, tmp_path, monkeypatch):
    """FastAPI TestClient with overridden DB dependency and temporary output directory."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override database dependency and output directory
    app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr(settings, "OUTPUT_DIR", tmp_path)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
