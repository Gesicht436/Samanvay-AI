"""
Task 18 — server-side session authentication & lifecycle tests (API level).

Proves the session security properties end-to-end through the real
application flow (login endpoint, HttpOnly cookie, server-side AuthSession):

A. successful authentication creates a server-side session + secure cookie
B. missing session cookie -> 401
C. unknown/malformed session secret -> 401 + cookie cleared
D. expired session -> 401 + cookie cleared
E. revoked session -> 401 + cookie cleared
F. logout revokes server-side, blocks further use, idempotent
G. pre-authentication session cannot become the authenticated session
H. the raw session secret is never stored (SHA-256 digest only)
I. actual response-cookie attributes (name/HttpOnly/SameSite/Path/Secure/Domain)
J. disabled/unapproved accounts cannot use an existing session
K. no JWT/Bearer/OIDC alternate authentication path exists

Conventions (see tests/api/test_auth_api.py and
test_auth5j3_account_provisioning.py):

* the real application lifespan runs (DB init + seed users); no
  authentication/authorization dependency is mocked or overridden;
* tests that touch PostgreSQL are BLOCKED (never PASS) when the database is
  unavailable at localhost:5432 — Runbook sections 4, 16 and 22;
* the small static subset (B/K behavior) needs no database and always runs.

Deliberately NOT tested here (unresolved policy — not invented by Task 18):
idle timeout (D-005-01) and concurrent-session limits (D-005-02). The
concurrency test below only pins the *existing* unrestricted behavior.
"""

import base64
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.core.config import settings
from backend.app.models.base import SessionLocal
from backend.app.models.tables import AuthSession, SecurityEvent, User
from backend.app.schemas.auth import DEFAULT_SEED_PASSWORD
from backend.app.services import auth_session_service as session_service

REPO_ROOT = Path(__file__).resolve().parents[2]
ORIGIN = settings.allowed_origins_list[0]
ME_PATH = "/api/v1/auth/me"
LOGIN_PATH = "/api/v1/auth/login"
LOGOUT_PATH = "/api/v1/auth/logout"
CSRF_PATH = "/api/v1/auth/csrf"

# Static client WITHOUT lifespan: DB-free tests only (never used for
# anything that reaches the database).
static_client = TestClient(app)


@pytest.fixture(scope="module")
def _application_lifespan():
    """Run the real application lifespan once (DB init + seed users)."""
    with TestClient(app):
        yield


@pytest.fixture()
def client(_application_lifespan):
    """Fresh client with an empty cookie jar, so every test starts anonymous."""
    return TestClient(app)


def _login(test_client, username):
    """Authenticate through the real login endpoint; return (response, secret)."""
    response = test_client.post(
        LOGIN_PATH,
        json={"username": username, "password": DEFAULT_SEED_PASSWORD},
    )
    assert response.status_code == 200, response.text
    secret = test_client.cookies.get(settings.session_cookie_name)
    assert secret, "login must establish the server-side session cookie"
    return response, secret


def _set_cookie_headers(response) -> list:
    """Raw Set-Cookie header lines of an httpx response."""
    return response.headers.get_list("set-cookie")


def _cookie_header(response):
    """Return (head, attrs) of the application session cookie, else (None, {})."""
    for header in _set_cookie_headers(response):
        if header.startswith(settings.session_cookie_name + "="):
            parts = [p.strip() for p in header.split(";")]
            attrs = {}
            for part in parts[1:]:
                key, _, value = part.partition("=")
                attrs[key.strip().lower()] = value.strip()
            return parts[0], attrs
    return None, {}


def _expected_hash(secret: str) -> str:
    raw = base64.urlsafe_b64decode(secret + "=" * (-len(secret) % 4))
    return hashlib.sha256(raw).hexdigest()


def _session_row_by_secret(db, secret: str):
    """Look up the AuthSession exactly the way the server does: by SHA-256 hash."""
    return (
        db.query(AuthSession)
        .filter(AuthSession.session_token_hash == _expected_hash(secret))
        .first()
    )


def _login_failures(db, *, session_id=None):
    query = db.query(SecurityEvent).filter(
        SecurityEvent.event_type == "LOGIN_FAILURE",
        SecurityEvent.success.is_(False),
    )
    if session_id is None:
        query = query.filter(SecurityEvent.session_id.is_(None))
    else:
        query = query.filter(SecurityEvent.session_id == session_id)
    return query.all()


# ── B / K: static tests (no database required) ───────────────────────────────

def test_missing_session_cookie_returns_401():
    """B: no cookie on a required route -> plain 401 with nothing to clear."""
    response = static_client.get(ME_PATH)
    assert response.status_code == 401
    assert response.headers.get_list("set-cookie") == []
    assert "session cookie" in response.json()["detail"]


def test_bearer_authorization_header_is_not_an_authentication_path():
    """K: Authorization: Bearer carries no authority — only the cookie does."""
    fake_secret = session_service.generate_session_secret()
    response = static_client.get(
        ME_PATH, headers={"Authorization": f"Bearer {fake_secret}"}
    )
    assert response.status_code == 401
    assert "session cookie" in response.json()["detail"]


def test_no_legacy_authentication_routes_registered():
    """K: no OIDC/OAuth/Google/SSO/SAML/token endpoint exists on the app."""
    paths = {getattr(route, "path", "") for route in app.routes}
    # /docs/oauth2-redirect is FastAPI's own Swagger-UI redirect scaffolding
    # (no OAuth flow is registered; the route disappears in production where
    # docs are disabled — D-5J.3-4). It authenticates nothing.
    framework_doc_routes = {"/docs/oauth2-redirect"}
    forbidden = [
        p for p in paths
        if p not in framework_doc_routes
        and re.search(r"(oauth|oidc|google|sso|saml|jwks|/token)", p, re.I)
    ]
    assert forbidden == [], f"legacy authentication routes registered: {forbidden}"


def test_backend_sources_have_no_jwt_or_bearer_auth_machinery():
    """K: no executable JWT/Bearer/OIDC machinery in backend Python sources."""
    forbidden = re.compile(
        r"(HTTPBearer|OAuth2PasswordBearer|HTTPAuthorizationCredentials"
        r"|security_bearer|decode_access_token|create_access_token"
        r"|import\s+jwt|from\s+jwt|import\s+jose|from\s+jose)"
    )
    offenders = []
    for path in (REPO_ROOT / "backend").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), 1):
            if forbidden.search(line):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{line_no}")
    assert offenders == [], f"legacy authentication machinery found: {offenders}"


def test_frontend_sources_have_no_bearer_or_jwt_credentials():
    """K: the frontend holds no browser-readable token credential."""
    forbidden = re.compile(
        r"(['\"]Bearer\s)|\bjwt\.decode\b|decode_access_token|create_access_token"
    )
    src_dir = REPO_ROOT / "frontend" / "src"
    offenders = []
    for pattern in ("*.ts", "*.tsx"):
        for path in src_dir.rglob(pattern):
            if "node_modules" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), 1):
                if forbidden.search(line):
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{line_no}")
    assert offenders == [], f"browser-readable credential handling found: {offenders}"


def test_no_test_time_dependency_overrides_for_authentication():
    """K: the suite exercises the real session stack; nothing is faked."""
    assert app.dependency_overrides == {}


# ── A: successful authentication ──────────────────────────────────────────────

def test_successful_authentication_establishes_server_side_session(client):
    """A: login creates one AuthSession + SESSION_CREATED/LOGIN_SUCCESS, cookie works."""
    response, secret = _login(client, "engineer_oil")
    data = response.json()
    # Cookie contract: no bearer/JWT material anywhere in the body.
    assert "access_token" not in data
    assert "token_type" not in data

    # The login response carries the application cookie.
    head, _attrs = _cookie_header(response)
    assert head == f"{settings.session_cookie_name}={secret}"

    db = SessionLocal()
    try:
        row = _session_row_by_secret(db, secret)
        assert row is not None, "login must persist a server-side AuthSession"
        assert row.revoked_at is None

        # Absolute expiry uses the configured default — an existing, documented
        # value (SESSION_ABSOLUTE_EXPIRE_MINUTES); Task 18 invents none.
        expires = row.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        ttl = timedelta(minutes=settings.session_absolute_expire_minutes)
        skew = abs((expires - datetime.now(timezone.utc)) - ttl)
        assert skew <= timedelta(minutes=5)

        # Telemetry: authoritative creation events, no secrets.
        events = (
            db.query(SecurityEvent)
            .filter(SecurityEvent.session_id == row.id)
            .all()
        )
        types = {e.event_type for e in events}
        assert {"SESSION_CREATED", "LOGIN_SUCCESS"} <= types
        assert all(e.success for e in events)
        assert secret not in json.dumps(
            [{e.event_type: e.event_metadata} for e in events], default=str
        )

        # Authenticated request succeeds and updates last_seen_at (approved
        # design element: idle *tracking* — enforcement is unresolved).
        first_seen = row.last_seen_at
        if first_seen.tzinfo is None:
            first_seen = first_seen.replace(tzinfo=timezone.utc)
        me = client.get(ME_PATH)
        assert me.status_code == 200, me.text
        assert me.json()["username"] == "engineer_oil"
        db.refresh(row)
        last_seen = row.last_seen_at
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        assert last_seen > first_seen, "authenticated use must touch last_seen_at"
    finally:
        db.close()


# ── I: actual response-cookie attributes ──────────────────────────────────────

def test_login_response_cookie_attributes(client):
    """I: HttpOnly + SameSite=Lax + Path=/ + host-only + Secure per environment."""
    response, secret = _login(client, "stores_hpcl")
    head, attrs = _cookie_header(response)
    assert head == f"{settings.session_cookie_name}={secret}"
    assert "httponly" in attrs
    assert attrs.get("samesite", "").lower() == "lax"
    assert attrs.get("path") == "/"
    assert "domain" not in attrs, "session cookie must be host-only (no Domain)"
    assert ("secure" in attrs) == settings.cookie_secure
    assert int(attrs.get("max-age", 0)) > 0
    assert attrs.get("expires"), "cookie must carry the session expiry"


# ── H: raw secret protection ─────────────────────────────────────────────────

def test_raw_session_secret_is_never_stored_in_database(client):
    """H: PostgreSQL contains only the SHA-256 digest — never the raw secret."""
    _response, secret = _login(client, "stores_oil")
    db = SessionLocal()
    try:
        row = _session_row_by_secret(db, secret)
        assert row is not None
        # The stored value is exactly SHA-256(raw bytes), lowercase 64-hex.
        assert row.session_token_hash == _expected_hash(secret)
        assert len(row.session_token_hash) == 64
        assert set(row.session_token_hash) <= set("0123456789abcdef")
        assert row.session_token_hash != secret
        # The raw secret appears in no stored column of the session row.
        for value in (
            str(row.id),
            str(row.session_token_hash),
            str(row.user_id),
            str(row.ip_address),
            str(row.user_agent),
        ):
            assert secret not in value
        # Nor in any SecurityEvent emitted for this session.
        events = (
            db.query(SecurityEvent)
            .filter(SecurityEvent.session_id == row.id)
            .all()
        )
        blob = json.dumps([e.event_metadata for e in events], default=str)
        assert secret not in blob
        assert row.session_token_hash not in blob
    finally:
        db.close()


