"""
Pytest fixtures за тестове.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.models.user import User
from app.models.region import Region
from app.models.scene import Scene
from app.models.index_type import IndexType
from app.models.index_value import IndexValue
from app.main import app
from app.core.security import create_access_token, hash_password

# Тестова база данни (SQLite in-memory)
# Забележка: GeoAlchemy2 изисква PostGIS, но за тестове използваме SQLite
# В production трябва да се използва# Test database setup
# SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1401@db:5432/blacksea_monitor_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Session:
    """Създава тестова база данни за всеки тест."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db: Session) -> TestClient:
    """Създава TestClient с override на get_db."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Създава тестов потребител."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpass123"),
        role="viewer"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin(db: Session) -> User:
    """Създава тестов администратор."""
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("adminpass123"),
        role="admin"
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def test_researcher(db: Session) -> User:
    """Създава тестов изследовател."""
    researcher = User(
        username="researcher",
        email="researcher@example.com",
        password_hash=hash_password("researcherpass123"),
        role="researcher"
    )
    db.add(researcher)
    db.commit()
    db.refresh(researcher)
    return researcher


@pytest.fixture
def auth_headers_viewer(test_user: User) -> dict:
    """Връща auth headers за viewer."""
    token = create_access_token({"sub": test_user.username, "role": test_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_admin(test_admin: User) -> dict:
    """Връща auth headers за admin."""
    token = create_access_token({"sub": test_admin.username, "role": test_admin.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_researcher(test_researcher: User) -> dict:
    """Връща auth headers за researcher."""
    token = create_access_token({"sub": test_researcher.username, "role": test_researcher.role})
    return {"Authorization": f"Bearer {token}"}

