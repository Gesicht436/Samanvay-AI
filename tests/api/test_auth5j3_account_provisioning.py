"""
AUTH-5J.3 focused tests — account-provisioning telemetry and production
documentation/OpenAPI gating.

Scope (per the AUTH-5J.3 architecture decisions):

1. ``POST /api/v1/auth/users`` emits exactly one ``ACCOUNT_PROVISIONED``
   event, identifying the authenticated actor, the actor session and the
   target account, committed atomically with the ``User`` INSERT, with no
   secrets in event metadata.
2. A denied (anonymous) provisioning attempt writes no event and creates no
   account.
3. Production deployments expose no ``/docs``, ``/redoc`` or
   ``/openapi.json``; non-production keeps the existing behavior.
4. Scope guard: no account disable/enable routes exist (reserved pending
   future architectural specification — decision D-5J.3-2).

Authentication uses the real application flow: admin login session cookie,
``GET /auth/csrf`` synchronizer token, and the configured Origin allowlist.
No authentication or authorization dependency is mocked or overridden
(failure injection in the atomicity test targets telemetry persistence only).
"""

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.core.config import settings
from backend.app.models.base import SessionLocal
from backend.app.models.tables import SecurityEvent, User
from backend.app.schemas.auth import DEFAULT_SEED_PASSWORD
from backend.app.services import auth_session_service as session_service

REPO_ROOT = Path(__file__).resolve().parents[2]


# ── Real application fixtures (mirrors tests/api/test_match_api.py) ─────────

@pytest.fixture(scope="module")
def _application_lifespan():
    """Run the real application lifespan once (DB init + seed users)."""
    with TestClient(app):
        yield


@pytest.fixture()
def client(_application_lifespan):
    """Fresh client with an empty cookie jar, so every test starts anonymous."""
    return TestClient(app)


@pytest.fixture(scope="module")
def _admin_session(_application_lifespan):
    """One real SUPER_ADMIN login for the whole module (rate-limit friendly).

    Returns exactly what a browser would hold after login: the raw session
    cookie value, the session-bound CSRF token, and the admin user id.
    """
    login_client = TestClient(app)
    response = login_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": DEFAULT_SEED_PASSWORD},
    )
    assert response.status_code == 200, response.text
    cookie = login_client.cookies.get(settings.session_cookie_name)
    assert cookie, "login must establish the server-side session cookie"
    csrf = login_client.get("/api/v1/auth/csrf").json()["csrf_token"]
    return {"cookie": cookie, "csrf": csrf, "admin_id": response.json()["id"]}


def _admin_headers(admin):
    """CSRF headers for an unsafe request: synchronizer token + allowlisted Origin."""
    return {
        "X-CSRF-Token": admin["csrf"],
        "Origin": settings.allowed_origins_list[0],
    }


def _authenticate(client, admin):
    """Present the admin's server-side session cookie on a fresh client."""
    client.cookies.set(settings.session_cookie_name, admin["cookie"])


def _provision_payload():
    token = uuid.uuid4().hex[:10]
    return {
        "username": f"j3_{token}",
        "password": "ProvisionTest@2026",
        "full_name": "Er. 5J.3 Test Engineer",
        "email": f"j3_{token}@oilindia.in",
        "role": "SITE_ENGINEER",
        "cpse": "OIL",
        "depot_id": "DEPOT-OIL-DLJ",
    }


def _events_for_username(username):
    """Return plain-value ACCOUNT_PROVISIONED events targeting ``username``."""
    db = SessionLocal()
    try:
        rows = (
            db.query(SecurityEvent)
            .filter(SecurityEvent.event_type == "ACCOUNT_PROVISIONED")
            .all()
        )
        return [
            {
                "user_id": row.user_id,
                "session_id": row.session_id,
                "success": row.success,
                "metadata": dict(row.event_metadata or {}),
            }
            for row in rows
            if (row.event_metadata or {}).get("target_username") == username
        ]
    finally:
        db.close()


def _user_exists(username):
    db = SessionLocal()
    try:
        return (
            db.query(User).filter(User.username == username).first() is not None
        )
    finally:
        db.close()



# ── 1. ACCOUNT_PROVISIONED telemetry ────────────────────────────────────────

def test_account_provisioned_event_constant():
    """The amended frozen event vocabulary carries the exact event type."""
    assert session_service.EVENT_ACCOUNT_PROVISIONED == "ACCOUNT_PROVISIONED"


def test_provision_emits_exactly_one_account_provisioned_event(
    client, _admin_session
):
    payload = _provision_payload()
    _authenticate(client, _admin_session)

    response = client.post(
        "/api/v1/auth/users",
        json=payload,
        headers=_admin_headers(_admin_session),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["is_active"] is True
    assert body["is_approved"] is False, (
        "provisioning must leave the account unapproved"
    )

    events = _events_for_username(payload["username"])
    assert len(events) == 1, (
        "exactly one ACCOUNT_PROVISIONED event must be persisted per "
        "successful provisioning"
    )
    event = events[0]
    assert event["success"] is True

    # Actor identity: the authenticated provisioning administrator.
    assert event["user_id"] == _admin_session["admin_id"]

    # Actor session: must be the live session resolved from the real cookie.
    db = SessionLocal()
    try:
        session = session_service.resolve_session(db, _admin_session["cookie"])
        assert session is not None
        assert event["session_id"] == session.id

        # Target account identity in sanitized metadata — nothing else.
        assert set(event["metadata"]) == {"target_user_id", "target_username"}
        assert event["metadata"]["target_user_id"] == body["id"]
        assert event["metadata"]["target_username"] == payload["username"]

        # No secret of any kind may enter the event metadata.
        serialized = json.dumps(event["metadata"])
        assert payload["password"] not in serialized
        assert session.session_token_hash not in serialized
        assert _admin_session["csrf"] not in serialized

        target = db.query(User).filter(User.id == body["id"]).first()
        assert target is not None
        assert target.hashed_password not in serialized
    finally:
        db.close()


def test_provision_telemetry_failure_rolls_back_user_insert(
    client, _admin_session, monkeypatch
):
    """Atomicity: if the event cannot be staged, the User INSERT must not
    survive — no account may exist without its provisioning telemetry."""
    payload = _provision_payload()
    _authenticate(client, _admin_session)

    def _fail(*args, **kwargs):
        raise RuntimeError("telemetry staging unavailable (injected)")

    monkeypatch.setattr(
        "backend.app.api.routers.auth.session_service.record_security_event",
        _fail,
    )
    response = client.post(
        "/api/v1/auth/users",
        json=payload,
        headers=_admin_headers(_admin_session),
    )
    assert response.status_code == 409, response.text

    assert not _user_exists(payload["username"]), (
        "failed telemetry must roll back the user INSERT in the same "
        "transaction"
    )
    assert _events_for_username(payload["username"]) == []


def test_anonymous_provisioning_denied_without_event(client):
    """Unauthenticated provisioning must fail closed and write no event."""
    payload = _provision_payload()
    response = client.post(
        "/api/v1/auth/users",
        json=payload,
        headers={"Origin": settings.allowed_origins_list[0]},
    )
    assert response.status_code == 401
    assert not _user_exists(payload["username"])
    assert _events_for_username(payload["username"]) == []


# ── 2. Production documentation/OpenAPI gating (D-5J.3-4) ──────────────────

def test_docs_available_in_non_production(client):
    """Non-production keeps the existing documentation/OpenAPI behavior."""
    assert not settings.is_production, (
        "this test suite runs in a non-production environment"
    )
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"
    assert app.openapi_url == "/openapi.json"
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_docs_disabled_in_production():
    """APP_ENV=production must construct the app without docs/redoc/openapi."""
    script = (
        "from fastapi.testclient import TestClient\n"
        "from backend.main import app\n"
        "assert app.docs_url is None, app.docs_url\n"
        "assert app.redoc_url is None, app.redoc_url\n"
        "assert app.openapi_url is None, app.openapi_url\n"
        "c = TestClient(app)\n"
        "for path in ('/docs', '/redoc', '/openapi.json'):\n"
        "    r = c.get(path)\n"
        "    assert r.status_code == 404, (path, r.status_code)\n"
        "print('PRODUCTION_DOCS_DISABLED')\n"
    )
    env = dict(os.environ)
    env["APP_ENV"] = "production"
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, result.stderr
    assert "PRODUCTION_DOCS_DISABLED" in result.stdout


# ── 3. Scope guard (D-5J.3-2) ──────────────────────────────────────────────

def test_no_account_disable_or_enable_routes_registered():
    """Disable/enable remain reserved: no such routes may exist (5J.3 scope)."""
    paths = {getattr(route, "path", "") for route in app.routes}
    forbidden = [p for p in paths if p.endswith(("/disable", "/enable"))]
    assert forbidden == [], f"reserved disable/enable routes registered: {forbidden}"
