"""
Тестове за Team Management – обхващат всички CRUD операции за екипи и членства.
Използва FastAPI TestClient с SQLite в паметта.
Създава само необходимите таблици (User, Team, TeamMembership), за да
се избегнат GeoAlchemy2/PostGIS зависимости от модела Region.
"""
import sys
import os

# Добавяне на backend директорията към PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
from datetime import datetime

# ---------- Собствена тестова база и модели (без GeoAlchemy2) ----------

class TestBase(DeclarativeBase):
    pass


class TestUser(TestBase):
    """Опростен User модел за тестовата SQLite база."""
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="viewer")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestTeam(TestBase):
    """Опростен Team модел за тестовата SQLite база."""
    __tablename__ = "team"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestTeamMembership(TestBase):
    """Опростен TeamMembership модел за тестовата SQLite база."""
    __tablename__ = "team_membership"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    team_id = Column(Integer, nullable=False)
    role = Column(String(20), nullable=False, default="member")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Импорти от приложението
from app.core.database import get_db
from app.core.security import hash_password, create_access_token
from app.main import app


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ---------- Помощни функции ----------

def create_test_user(db, username, email, role="admin"):
    """Създава тестов потребител директно в базата."""
    hashed = hash_password("testpass123")
    db.execute(
        TestUser.__table__.insert().values(
            username=username,
            email=email,
            password_hash=hashed,
            role=role,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    )
    db.commit()
    user = db.query(TestUser).filter(TestUser.username == username).first()
    return user


def get_auth_headers(user):
    """Генерира JWT token и връща Authorization header."""
    token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


# ---------- Fixtures ----------

@pytest.fixture(autouse=True)
def setup_db():
    """Създава само необходимите таблици (без GeoAlchemy2)."""
    TestBase.metadata.create_all(bind=test_engine)
    yield
    TestBase.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_user(db):
    return create_test_user(db, "admin_user", "admin@test.com", "admin")


@pytest.fixture
def viewer_user(db):
    return create_test_user(db, "viewer_user", "viewer@test.com", "viewer")


@pytest.fixture
def researcher_user(db):
    return create_test_user(db, "researcher_user", "researcher@test.com", "researcher")


# ================================================================
#                     ТЕСТОВЕ ЗА ЕКИПИ (TEAMS)
# ================================================================

class TestCreateTeam:

    def test_create_team_success(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        response = client.post("/teams/", json={"name": "Varna Bay Team"}, headers=headers)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["name"] == "Varna Bay Team"
        assert "id" in data

    def test_create_team_duplicate_name(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        client.post("/teams/", json={"name": "Duplicate Team"}, headers=headers)
        response = client.post("/teams/", json={"name": "Duplicate Team"}, headers=headers)
        assert response.status_code == 409

    def test_create_team_auto_adds_creator(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Auto Member Team"}, headers=headers)
        team_id = resp.json()["id"]

        members_resp = client.get(f"/teams/{team_id}/members", headers=headers)
        assert members_resp.status_code == 200
        members = members_resp.json()
        assert len(members) == 1
        assert members[0]["user_id"] == admin_user.id
        assert members[0]["role"] == "admin"

    def test_create_team_unauthenticated(self, client):
        response = client.post("/teams/", json={"name": "Unauth Team"})
        assert response.status_code == 401


class TestReadTeams:

    def test_list_teams_empty(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        response = client.get("/teams/", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_teams_with_data(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        client.post("/teams/", json={"name": "Team A"}, headers=headers)
        client.post("/teams/", json={"name": "Team B"}, headers=headers)

        response = client.get("/teams/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = {t["name"] for t in data}
        assert "Team A" in names
        assert "Team B" in names

    def test_get_team_by_id(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Specific Team"}, headers=headers)
        team_id = resp.json()["id"]

        response = client.get(f"/teams/{team_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Specific Team"

    def test_get_team_not_found(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        response = client.get("/teams/9999", headers=headers)
        assert response.status_code == 404


class TestUpdateTeam:

    def test_update_team_name(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Old Name"}, headers=headers)
        team_id = resp.json()["id"]

        response = client.put(f"/teams/{team_id}", json={"name": "New Name"}, headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_update_team_not_found(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        response = client.put("/teams/9999", json={"name": "Ghost"}, headers=headers)
        assert response.status_code == 404

    def test_update_team_forbidden_for_viewer(self, client, admin_user, viewer_user):
        admin_headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Admin Team"}, headers=admin_headers)
        team_id = resp.json()["id"]

        viewer_headers = get_auth_headers(viewer_user)
        response = client.put(f"/teams/{team_id}", json={"name": "Hack"}, headers=viewer_headers)
        assert response.status_code == 403

    def test_update_team_duplicate_name(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        client.post("/teams/", json={"name": "TeamX"}, headers=headers)
        resp2 = client.post("/teams/", json={"name": "TeamY"}, headers=headers)
        team_y_id = resp2.json()["id"]

        response = client.put(f"/teams/{team_y_id}", json={"name": "TeamX"}, headers=headers)
        assert response.status_code == 409


class TestDeleteTeam:

    def test_delete_team_success(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "To Delete"}, headers=headers)
        team_id = resp.json()["id"]

        response = client.delete(f"/teams/{team_id}", headers=headers)
        assert response.status_code == 204

        get_resp = client.get(f"/teams/{team_id}", headers=headers)
        assert get_resp.status_code == 404

    def test_delete_team_not_found(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        response = client.delete("/teams/9999", headers=headers)
        assert response.status_code == 404

    def test_delete_team_forbidden_for_viewer(self, client, admin_user, viewer_user):
        admin_headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Protected"}, headers=admin_headers)
        team_id = resp.json()["id"]

        viewer_headers = get_auth_headers(viewer_user)
        response = client.delete(f"/teams/{team_id}", headers=viewer_headers)
        assert response.status_code == 403


# ================================================================
#               ТЕСТОВЕ ЗА ЧЛЕНСТВО В ЕКИПИ (MEMBERS)
# ================================================================

class TestAddMember:

    def test_add_member_success(self, client, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "My Team"}, headers=headers)
        team_id = resp.json()["id"]

        response = client.post(
            f"/teams/{team_id}/members",
            json={"user_id": viewer_user.id, "team_id": team_id, "role": "member"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == viewer_user.id
        assert data["role"] == "member"

    def test_add_member_duplicate(self, client, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Dup Team"}, headers=headers)
        team_id = resp.json()["id"]

        client.post(
            f"/teams/{team_id}/members",
            json={"user_id": viewer_user.id, "team_id": team_id, "role": "member"},
            headers=headers,
        )
        response = client.post(
            f"/teams/{team_id}/members",
            json={"user_id": viewer_user.id, "team_id": team_id, "role": "member"},
            headers=headers,
        )
        assert response.status_code == 409

    def test_add_member_user_not_found(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Ghost User Team"}, headers=headers)
        team_id = resp.json()["id"]

        response = client.post(
            f"/teams/{team_id}/members",
            json={"user_id": 9999, "team_id": team_id, "role": "member"},
            headers=headers,
        )
        assert response.status_code == 404

    def test_add_member_team_not_found(self, client, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        response = client.post(
            "/teams/9999/members",
            json={"user_id": viewer_user.id, "team_id": 9999, "role": "member"},
            headers=headers,
        )
        assert response.status_code == 404


class TestReadMembers:

    def test_read_members_with_creator(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Creator Team"}, headers=headers)
        team_id = resp.json()["id"]

        response = client.get(f"/teams/{team_id}/members", headers=headers)
        assert response.status_code == 200
        members = response.json()
        assert len(members) >= 1

    def test_read_members_multiple(self, client, admin_user, viewer_user, researcher_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Multi Team"}, headers=headers)
        team_id = resp.json()["id"]

        client.post(
            f"/teams/{team_id}/members",
            json={"user_id": viewer_user.id, "team_id": team_id, "role": "member"},
            headers=headers,
        )
        client.post(
            f"/teams/{team_id}/members",
            json={"user_id": researcher_user.id, "team_id": team_id, "role": "moderator"},
            headers=headers,
        )

        response = client.get(f"/teams/{team_id}/members", headers=headers)
        assert response.status_code == 200
        members = response.json()
        assert len(members) == 3

    def test_read_members_team_not_found(self, client, admin_user):
        headers = get_auth_headers(admin_user)
        response = client.get("/teams/9999/members", headers=headers)
        assert response.status_code == 404


class TestUpdateMemberRole:

    def test_update_role_success(self, client, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Role Team"}, headers=headers)
        team_id = resp.json()["id"]

        client.post(
            f"/teams/{team_id}/members",
            json={"user_id": viewer_user.id, "team_id": team_id, "role": "member"},
            headers=headers,
        )

        response = client.put(
            f"/teams/{team_id}/members/{viewer_user.id}",
            json={"role": "moderator"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["role"] == "moderator"

    def test_update_role_not_a_member(self, client, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "No Member Team"}, headers=headers)
        team_id = resp.json()["id"]

        response = client.put(
            f"/teams/{team_id}/members/{viewer_user.id}",
            json={"role": "moderator"},
            headers=headers,
        )
        assert response.status_code == 404

    def test_update_role_forbidden_for_viewer(self, client, admin_user, viewer_user):
        admin_headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Restricted Team"}, headers=admin_headers)
        team_id = resp.json()["id"]

        viewer_headers = get_auth_headers(viewer_user)
        response = client.put(
            f"/teams/{team_id}/members/{admin_user.id}",
            json={"role": "member"},
            headers=viewer_headers,
        )
        assert response.status_code == 403


class TestRemoveMember:

    def test_remove_member_success(self, client, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Remove Team"}, headers=headers)
        team_id = resp.json()["id"]

        client.post(
            f"/teams/{team_id}/members",
            json={"user_id": viewer_user.id, "team_id": team_id, "role": "member"},
            headers=headers,
        )

        response = client.delete(f"/teams/{team_id}/members/{viewer_user.id}", headers=headers)
        assert response.status_code == 204

        members_resp = client.get(f"/teams/{team_id}/members", headers=headers)
        member_ids = [m["user_id"] for m in members_resp.json()]
        assert viewer_user.id not in member_ids

    def test_remove_member_not_found(self, client, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "No Remove Team"}, headers=headers)
        team_id = resp.json()["id"]

        response = client.delete(f"/teams/{team_id}/members/{viewer_user.id}", headers=headers)
        assert response.status_code == 404

    def test_remove_member_team_not_found(self, client, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        response = client.delete(f"/teams/9999/members/{viewer_user.id}", headers=headers)
        assert response.status_code == 404

    def test_remove_member_forbidden_for_viewer(self, client, admin_user, viewer_user):
        admin_headers = get_auth_headers(admin_user)
        resp = client.post("/teams/", json={"name": "Locked Team"}, headers=admin_headers)
        team_id = resp.json()["id"]

        viewer_headers = get_auth_headers(viewer_user)
        response = client.delete(f"/teams/{team_id}/members/{admin_user.id}", headers=viewer_headers)
        assert response.status_code == 403


# ================================================================
#                 ИНТЕГРАЦИОНЕН E2E ТЕСТ
# ================================================================

class TestTeamManagementE2E:

    def test_full_workflow(self, client, admin_user, viewer_user, researcher_user):
        """Full lifecycle: create -> add members -> change role -> remove -> rename -> delete."""
        headers = get_auth_headers(admin_user)

        # 1. Create team
        resp = client.post("/teams/", json={"name": "E2E Team"}, headers=headers)
        assert resp.status_code == 201
        team_id = resp.json()["id"]

        # 2. Creator is admin member
        members = client.get(f"/teams/{team_id}/members", headers=headers).json()
        assert len(members) == 1
        assert members[0]["role"] == "admin"

        # 3. Add viewer and researcher
        r1 = client.post(
            f"/teams/{team_id}/members",
            json={"user_id": viewer_user.id, "team_id": team_id, "role": "member"},
            headers=headers,
        )
        assert r1.status_code == 200
        r2 = client.post(
            f"/teams/{team_id}/members",
            json={"user_id": researcher_user.id, "team_id": team_id, "role": "member"},
            headers=headers,
        )
        assert r2.status_code == 200

        members = client.get(f"/teams/{team_id}/members", headers=headers).json()
        assert len(members) == 3

        # 4. Change researcher role to moderator
        resp = client.put(
            f"/teams/{team_id}/members/{researcher_user.id}",
            json={"role": "moderator"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "moderator"

        # 5. Remove viewer
        resp = client.delete(f"/teams/{team_id}/members/{viewer_user.id}", headers=headers)
        assert resp.status_code == 204

        members = client.get(f"/teams/{team_id}/members", headers=headers).json()
        assert len(members) == 2

        # 6. Rename team
        resp = client.put(f"/teams/{team_id}", json={"name": "E2E Team Renamed"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "E2E Team Renamed"

        # 7. Delete team
        resp = client.delete(f"/teams/{team_id}", headers=headers)
        assert resp.status_code == 204

        # 8. Confirm deleted
        resp = client.get(f"/teams/{team_id}", headers=headers)
        assert resp.status_code == 404

        # 9. List is empty
        resp = client.get("/teams/", headers=headers)
        assert len(resp.json()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
