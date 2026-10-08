"""
Public self-registration retirement tests (reconciled by Task 16A).

POST /api/v1/auth/signup intentionally does not exist: the legacy public
signup flow was removed (AUTH-006 Phase 2) and public registration is not
part of the current session-cookie authentication architecture. Account
provisioning is a backend-only, authenticated administrative capability.

These tests assert that no public signup route has been (re)introduced.
They require no database.
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_public_signup_post_route_is_retired():
    """POST /auth/signup must 404 — no public registration endpoint exists."""
    response = client.post(
        "/api/v1/auth/signup",
        json={"username": "should_not_exist", "password": "irrelevant"},
    )
    assert response.status_code == 404


def test_public_signup_get_route_is_retired():
    """GET /auth/signup must 404 — no signup surface exists in the API."""
    response = client.get("/api/v1/auth/signup")
    assert response.status_code == 404
