import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import hash_password

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Create test user
    test_user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpassword"),
        role="viewer"
    )
    db.add(test_user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def test_login_success():
    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure_and_rate_limit():
    # Attempt 5 times with wrong password
    for _ in range(5):
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401
    
    # 6th attempt should be rate limited
    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 429
    assert "Too many login attempts" in response.json()["detail"]

def test_refresh_token_success():
    # Login to get refresh token
    login_res = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpassword"}
    )
    refresh_token = login_res.json()["refresh_token"]
    
    # Refresh
    refresh_res = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token # Token rotation

def test_refresh_token_expired_or_invalid():
    # Invalid token
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401
    
    # Expired token (manual DB update for test)
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == "testuser").first()
    user.refresh_token = "some_token"
    user.refresh_token_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
    
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "some_token"}
    )
    assert response.status_code == 401
