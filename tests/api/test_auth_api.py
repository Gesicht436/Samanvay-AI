"""
Tests for Authentication & Role-Based Access Control (RBAC) API.

Verifies:
1. Seed users retrieval & password integrity.
2. Login credential verification and JWT Bearer token generation.
3. Multi-tenant CPSE/depot claim binding.
4. Unauthorized access prevention.
5. Idempotent user seeding.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.schemas.auth import DEFAULT_SEED_PASSWORD

client = TestClient(app)


def test_get_seed_users():
    """Verify endpoint provides all 8 seed persona accounts."""
    response = client.get("/api/v1/auth/seed-users")
    assert response.status_code == 200
    data = response.json()
    assert data["default_password"] == DEFAULT_SEED_PASSWORD
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


def test_login_successful_oil_engineer():
    """Verify engineer_oil can authenticate and receive a valid signed JWT."""
    # Register the user dynamically since auto-seeding is disabled
    client.post(
        "/api/v1/auth/signup",
        json={
            "username": "engineer_oil",
            "password": DEFAULT_SEED_PASSWORD,
            "full_name": "Er. Arindam Phukan",
            "email": "arindam.phukan@oilindia.in",
            "role": "SITE_ENGINEER",
            "cpse": "OIL",
            "depot_id": "DEPOT-OIL-DLJ"
        }
    )
    # Login as admin to approve
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": DEFAULT_SEED_PASSWORD}
    )
    admin_token = admin_login.json()["access_token"]
    
    users = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {admin_token}"}).json()
    user_id = next(u["id"] for u in users if u["username"] == "engineer_oil")
    client.post(f"/api/v1/auth/users/{user_id}/approve", headers={"Authorization": f"Bearer {admin_token}"})
    
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "engineer_oil", "password": DEFAULT_SEED_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    user = data["user"]
    assert user["username"] == "engineer_oil"
    assert user["role"] == "SITE_ENGINEER"
    assert user["cpse"] == "OIL"
    assert "OIL" in user["depot_id"]


def test_login_invalid_password():
    """Verify login fails with HTTP 401 on incorrect credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "engineer_oil", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_login_nonexistent_user():
    """Verify login fails with HTTP 401 for unknown username."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "non_existent_persona", "password": DEFAULT_SEED_PASSWORD},
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_get_current_user_me():
    """Verify /me returns caller profile claims from Bearer token."""
    # Register the user
    client.post(
        "/api/v1/auth/signup",
        json={
            "username": "stores_iocl",
            "password": DEFAULT_SEED_PASSWORD,
            "full_name": "Vikramaditya Rao",
            "email": "vikram.rao@indianoil.in",
            "role": "MATERIALS_MANAGER",
            "cpse": "IOCL",
            "depot_id": "DEPOT-IOCL-PNP"
        }
    )
    # Login as admin to approve
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": DEFAULT_SEED_PASSWORD}
    )
    admin_token = admin_login.json()["access_token"]
    
    users = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {admin_token}"}).json()
    user_id = next(u["id"] for u in users if u["username"] == "stores_iocl")
    client.post(f"/api/v1/auth/users/{user_id}/approve", headers={"Authorization": f"Bearer {admin_token}"})
    
    # Login as stores_iocl
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "stores_iocl", "password": DEFAULT_SEED_PASSWORD},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Access /me
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me = me_res.json()
    assert me["username"] == "stores_iocl"
    assert me["role"] == "MATERIALS_MANAGER"
    assert me["cpse"] == "IOCL"
    assert me["depot_id"] == "DEPOT-IOCL-PNP"


def test_get_me_unauthorized():
    """Verify /me rejects unauthenticated requests with HTTP 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_seed_endpoint_idempotency():
    """Verify /seed can be invoked repeatedly without conflict."""
    res1 = client.post("/api/v1/auth/seed")
    assert res1.status_code == 200
    assert res1.json()["status"] == "SUCCESS"

    res2 = client.post("/api/v1/auth/seed")
    assert res2.status_code == 200
    assert res2.json()["status"] == "SUCCESS"
    assert res2.json()["total_users"] >= 8
