import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("PRICING_PROVIDER", "mock")
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "")
os.environ.setdefault("LOCAL_STORAGE_DIR", "test_data/itineraries")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Plan
from app.db import session as db_session

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Point the app's session module at the test engine.
db_session.engine = engine
db_session.SessionLocal = TestingSession

from app.main import app  # noqa: E402
from app.db.session import get_db  # noqa: E402


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestingSession() as db:
        db.add_all(
            [
                Plan(name="Basic", api_limit=10),
                Plan(name="Standard", api_limit=25),
                Plan(name="Premium", api_limit=50),
            ]
        )
        db.commit()
    yield


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def user(client):
    resp = client.post(
        "/auth/signup",
        json={
            "email": "traveler@example.com",
            "password": "password123",
            "name": "Test Traveler",
            "plan": "Basic",
            "interests": ["museum", "park"],
        },
    )
    assert resp.status_code == 201, resp.text
    client.post("/auth/login", json={"email": "traveler@example.com", "password": "password123"})
    return resp.json()
