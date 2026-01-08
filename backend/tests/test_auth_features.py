import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import hash_password



def test_login_success(client, test_user):
    # test_user fixture creates user with password 'testpass123'
    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    # assert "refresh_token" in data  # Not implemented yet
    assert data["token_type"] == "bearer"

@pytest.mark.skip(reason="Rate limiting not implemented yet")
def test_login_failure_and_rate_limit(client, test_user):
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
        json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 429
    assert "Too many login attempts" in response.json()["detail"]

@pytest.mark.skip(reason="Refresh token not implemented yet")
def test_refresh_token_success(client, test_user):
    # Login to get refresh token
    login_res = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpass123"}
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

@pytest.mark.skip(reason="Refresh token not implemented yet")
def test_refresh_token_expired_or_invalid(client, test_user, db):
    # Invalid token
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401


