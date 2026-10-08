"""
Tests for the Authentication & RBAC API under the session-cookie contract.

Reconciled by Task 16A to match the actual implementation:

1. Seed persona listing with no credential disclosure.
2. POST /auth/login establishes a server-side session cookie and returns the
   user profile only — no JWT, no access_token, no token_type.
3. GET /auth/me resolves identity from the session cookie.
4. Unauthorized requests are rejected with HTTP 401.
5. The legacy public /auth/seed route is retired (404).

No JWT/Bearer/public-signup expectations remain.

Tests that exercise login/session persistence run the real application
lifespan (DB init + seed users), mirroring
tests/api/test_auth5j3_account_provisioning.py, and therefore require
PostgreSQL. They are BLOCKED (never PASS) when the database is unavailable.
Static/route-absence tests need no database.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.core.config import settings
from backend.app.schemas.auth import DEFAULT_SEED_PASSWORD

# No lifespan attached: static tests only. Never used for DB-dependent calls.
client = TestClient(app)


@pytest.fixture(scope="module")
def _application_lifespan():
    """Run the real application lifespan once (DB init + seed users)."""
    with TestClient(app):
        yield


def test_get_seed_users():
    """Endpoint lists seed personas and never discloses a shared password."""
    response = client.get("/api/v1/auth/seed-users")
    assert response.status_code == 200
    data = response.json()
    # The endpoint is strictly read-only: no default/shared password field.
    assert "default_password" not in data
    users = data["users"]
    assert len(users) >= 8
    usernames = {u["username"] for u in users}
    expected = {
        "engineer_oil",
        "stores_oil",
        "engineer_iocl",
        "stores_iocl",
        "tech_authority",
        "cisf_officer",
        "auditor",
        "admin",
    }
    assert expected.issubset(usernames)


def test_login_successful_oil_engineer(_application_lifespan):
    """Login sets a server-side session cookie; response is profile only."""
    session_client = TestClient(app)
    response = session_client.post(
        "/api/v1/auth/login",
        json={"username": "engineer_oil", "password": DEFAULT_SEED_PASSWORD},
    )
    assert response.status_code == 200, response.text
    data = response.json()

    # Cookie-setting contract: no bearer/JWT material in the body.
    assert "access_token" not in data
    assert "token_type" not in data

    assert data["username"] == "engineer_oil"
    assert data["role"] == "SITE_ENGINEER"
    assert data["cpse"] == "OIL"
    assert "OIL" in data["depot_id"]

    # The server established the session as an HttpOnly cookie.
    cookie = session_client.cookies.get(settings.session_cookie_name)
    assert cookie, "login must establish the server-side session cookie"


def test_login_invalid_password(_application_lifespan):
    """Login fails with HTTP 401 on incorrect credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "engineer_oil", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_login_nonexistent_user(_application_lifespan):
    """Login fails with HTTP 401 for unknown username (generic message)."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "non_existent_persona", "password": DEFAULT_SEED_PASSWORD},
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_get_current_user_me(_application_lifespan):
    """/auth/me returns the profile resolved from the session cookie."""
    session_client = TestClient(app)
    login = session_client.post(
        "/api/v1/auth/login",
        json={"username": "stores_iocl", "password": DEFAULT_SEED_PASSWORD},
    )
    assert login.status_code == 200, login.text

    # No Authorization header: identity comes exclusively from the cookie.
    me_res = session_client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    me = me_res.json()
    assert me["username"] == "stores_iocl"
    assert me["role"] == "MATERIALS_MANAGER"
    assert me["cpse"] == "IOCL"
    assert "IOCL" in me["depot_id"]


def test_get_me_unauthorized():
    """Verify /me rejects unauthenticated requests with HTTP 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_legacy_public_seed_route_retired():
    """The public POST /auth/seed route no longer exists (404)."""
    response = client.post("/api/v1/auth/seed", json={})
    assert response.status_code == 404
