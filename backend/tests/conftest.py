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
from app.core.security import create_access_token
from passlib.context import CryptContext

# Тестова база данни (SQLite in-memory)
# Забележка: GeoAlchemy2 изисква PostGIS, но за тестове използваме SQLite
# В production трябва да се използва PostgreSQL с PostGIS
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
        password_hash=pwd_context.hash("testpass123"),
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
        password_hash=pwd_context.hash("adminpass123"),
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
        password_hash=pwd_context.hash("researcherpass123"),
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

