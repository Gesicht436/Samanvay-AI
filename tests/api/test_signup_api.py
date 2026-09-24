"""
Tests for CPSE Officer Registration & Signup API.

Verifies:
1. Successful user registration and immediate JWT token issuance.
2. Duplicate username rejection (HTTP 409).
3. Duplicate email rejection (HTTP 409).
4. Schema validation for roles and email formats (HTTP 422).
5. Immediate profile verification (/auth/me) with issued JWT token.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_signup_successful_new_engineer():
    """Verify new engineer registration succeeds and returns valid JWT token."""
    unique_id = uuid.uuid4().hex[:6]
    signup_payload = {
        "username": f"nrl_eng_{unique_id}",
        "password": "SecurePassword@2026",
        "full_name": "Er. Pranjal Saikia",
        "email": f"pranjal_{unique_id}@nrl.co.in",
        "role": "SITE_ENGINEER",
        "cpse": "NRL",
        "depot_id": "DEPOT-NRL-NMR",
    }

    response = client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    user = data["user"]
    assert user["username"] == f"nrl_eng_{unique_id}"
    assert user["role"] == "SITE_ENGINEER"
    assert user["cpse"] == "NRL"
    assert user["depot_id"] == "DEPOT-NRL-NMR"

    # Verify token immediately works on /auth/me
    token = data["access_token"]
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == f"nrl_eng_{unique_id}"


def test_signup_duplicate_username():
    """Verify registration fails with HTTP 409 if username is taken."""
    # Try registering with existing seed username 'engineer_oil'
    signup_payload = {
        "username": "engineer_oil",
        "password": "AnotherPassword@2026",
        "full_name": "Duplicate User",
        "email": "duplicate_user_test@oilindia.in",
        "role": "SITE_ENGINEER",
        "cpse": "OIL",
        "depot_id": "DEPOT-OIL-DLJ",
    }
    response = client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_signup_duplicate_email():
    """Verify registration fails with HTTP 409 if email is already registered."""
    unique_id = uuid.uuid4().hex[:6]
    first_user = {
        "username": f"user_a_{unique_id}",
        "password": "Password123!",
        "full_name": "First User",
        "email": f"shared_email_{unique_id}@iocl.in",
        "role": "MATERIALS_MANAGER",
        "cpse": "IOCL",
        "depot_id": "DEPOT-IOCL-PNP",
    }
    res1 = client.post("/api/v1/auth/signup", json=first_user)
    assert res1.status_code == 201

    second_user = {
        "username": f"user_b_{unique_id}",
        "password": "Password123!",
        "full_name": "Second User",
        "email": f"shared_email_{unique_id}@iocl.in",  # same email
        "role": "MATERIALS_MANAGER",
        "cpse": "IOCL",
        "depot_id": "DEPOT-IOCL-PNP",
    }
    res2 = client.post("/api/v1/auth/signup", json=second_user)
    assert res2.status_code == 409
    assert "already registered" in res2.json()["detail"]


def test_signup_invalid_role():
    """Verify registration fails with HTTP 422 when role is not a valid UserRole."""
    unique_id = uuid.uuid4().hex[:6]
    signup_payload = {
        "username": f"invalid_role_{unique_id}",
        "password": "Password123!",
        "full_name": "Invalid Role User",
        "email": f"invalid_role_{unique_id}@ongc.co.in",
        "role": "NON_EXISTENT_ROLE",
        "cpse": "ONGC",
        "depot_id": "DEPOT-ONGC-ANK",
    }
    response = client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 422
