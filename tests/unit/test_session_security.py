"""
Task 18 — session security primitives (no database required).

Covers the database-free half of the session-hardening properties:

* CSPRNG session-secret generation (256-bit, unique, canonical)
* strict canonical base64url decoding of presented secrets
* SHA-256 hashing (stored digest never equals the raw secret)
* server-side session resolution outcome classification
  (live / malformed / unknown / expired / revoked)
* session cookie attribute construction, including the production
  ``__Host-samanvay_session`` prefix contract
* production rejection of an insecure cookie configuration
* sanitized SecurityEvent staging (no raw secrets in telemetry)

The resolution tests exercise the real ``auth_session_service`` logic against
a minimal stub of the SQLAlchemy ``query().filter().first()`` boundary so
they are deterministic and executable while PostgreSQL is unavailable
(Runbook sections 4 and 22). End-to-end HTTP behavior — including the
cookie actually issued by ``POST /auth/login`` — lives in
``tests/api/test_session_lifecycle.py``.
"""

import base64
import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Response
from pydantic import ValidationError

from backend.app.api.routers.auth import _clear_session_cookie, _set_session_cookie
from backend.app.core.config import Settings, settings
from backend.app.models.tables import AuthSession
from backend.app.services import auth_session_service as session_service


# ── Session-secret generation & hashing ───────────────────────────────────────

def test_generate_session_secret_is_256_bit_and_unique():
    """Session secrets come from the CSPRNG and are unpredictable per login."""
    secrets_seen = {session_service.generate_session_secret() for _ in range(20)}
    assert len(secrets_seen) == 20, "generated session secrets must never repeat"
    for secret in secrets_seen:
        assert isinstance(secret, str)
        # 32 random bytes as unpadded base64url -> 43 ASCII characters.
        assert len(secret) == 43
        assert len(session_service.decode_session_secret(secret)) == 32
        assert "=" not in secret


def test_decode_session_secret_rejects_malformed_values():
    """Only canonical unpadded-base64url 32-byte secrets decode."""
    valid = session_service.generate_session_secret()
    assert session_service.decode_session_secret(valid) is not None
    assert session_service.decode_session_secret(None) is None
    assert session_service.decode_session_secret("") is None
    assert session_service.decode_session_secret("!!!not-base64!!!") is None
    assert session_service.decode_session_secret("AAAA") is None  # wrong length
    assert session_service.decode_session_secret(valid + "=") is None  # padded
    assert session_service.decode_session_secret(valid[:-1]) is None  # truncated
    # Non-canonical alphabet (standard base64 '+' is not urlsafe).
    assert session_service.decode_session_secret(valid[:-1] + "+") is None


def test_hash_session_secret_is_sha256_of_raw_bytes():
    """The stored digest is SHA-256 of the raw bytes — never the secret itself."""
    secret = session_service.generate_session_secret()
    raw = base64.urlsafe_b64decode(secret + "=" * (-len(secret) % 4))
    digest = session_service.hash_session_secret(secret)
    assert digest == hashlib.sha256(raw).hexdigest()
    assert len(digest) == 64
    assert digest == digest.lower()
    assert set(digest) <= set("0123456789abcdef")
    assert secret not in digest and digest not in secret


def test_hash_session_secret_rejects_malformed_input():
    assert session_service.hash_session_secret(None) is None

# ── Server-side resolution outcomes ───────────────────────────────────────────

class _StubQuery:
    def __init__(self, row):
        self._row = row

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._row


class _StubDB:
    """Minimal stand-in for a SQLAlchemy Session at the query boundary."""

    def __init__(self, row):
        self._row = row

    def query(self, _model):
        return _StubQuery(self._row)


def _session_row(*, expires_in_minutes=15, revoked=False) -> AuthSession:
    now = datetime.now(timezone.utc)
    return AuthSession(
        id="00000000-0000-0000-0000-000000000018",
        session_token_hash="0" * 64,
        user_id=1,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(minutes=expires_in_minutes),
        revoked_at=now if revoked else None,
    )


def test_resolve_live_session_returns_session_and_live_outcome():
    row = _session_row()
    secret = session_service.generate_session_secret()
    resolved, outcome = session_service.resolve_session_with_outcome(_StubDB(row), secret)
    assert outcome == "live"
    assert resolved is row
    # Public helper keeps its original contract: None for non-live outcomes.
    assert session_service.resolve_session(_StubDB(row), secret) is row


def test_resolve_accepts_naive_expires_at_as_utc():
    row = _session_row()
    row.expires_at = row.expires_at.replace(tzinfo=None)  # naive DB value
    _, outcome = session_service.resolve_session_with_outcome(
        _StubDB(row), session_service.generate_session_secret()
    )
    assert outcome == "live"


def test_resolve_rejects_expired_session():
    for naive in (False, True):
        row = _session_row(expires_in_minutes=-1)
        if naive:
            row.expires_at = row.expires_at.replace(tzinfo=None)
        resolved, outcome = session_service.resolve_session_with_outcome(
            _StubDB(row), session_service.generate_session_secret()
        )
        assert outcome == "expired"
        assert resolved is row  # row kept only for telemetry attribution
        assert session_service.resolve_session(
            _StubDB(row), session_service.generate_session_secret()
        ) is None


def test_resolve_rejects_revoked_session():
    row = _session_row(revoked=True)
    resolved, outcome = session_service.resolve_session_with_outcome(
        _StubDB(row), session_service.generate_session_secret()
    )
    assert outcome == "revoked"
    assert resolved is row
    assert session_service.resolve_session(
        _StubDB(row), session_service.generate_session_secret()
    ) is None


def test_resolve_rejects_unknown_and_malformed_secrets():
    secret = session_service.generate_session_secret()
    resolved, outcome = session_service.resolve_session_with_outcome(_StubDB(None), secret)
    assert (resolved, outcome) == (None, "unknown")

    resolved, outcome = session_service.resolve_session_with_outcome(
        _StubDB(_session_row()), "definitely-not-a-session-secret"
    )
    assert (resolved, outcome) == (None, "malformed")
    assert session_service.resolve_session(_StubDB(None), secret) is None


# ── Cookie attribute construction ─────────────────────────────────────────────

def _cookie_attrs(header: str):
    parts = [p.strip() for p in header.split(";")]
    attrs = {}
    for part in parts[1:]:
        key, _, value = part.partition("=")
        attrs[key.strip().lower()] = value.strip()
    return parts[0], attrs


def _set_cookie_headers(response) -> list:
    """Raw Set-Cookie header lines (Starlette Headers API differs by class)."""
    if hasattr(response.headers, "get_list"):
        return response.headers.get_list("set-cookie")
    return response.headers.getlist("set-cookie")


def test_session_cookie_deletion_header_attributes():
    header = session_service.session_cookie_deletion_header()
    head, attrs = _cookie_attrs(header)
    assert head == settings.session_cookie_name + "="
    assert attrs.get("max-age") == "0"
    assert "1970" in attrs.get("expires", "")
    assert attrs.get("path") == "/"
    assert "httponly" in attrs
    assert attrs.get("samesite", "").lower() == "lax"
    assert "domain" not in attrs, "session cookie must stay host-only"
    assert ("secure" in attrs) == settings.cookie_secure


def test_set_session_cookie_attributes_non_production(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "development")
    response = Response()
    secret = session_service.generate_session_secret()
    row = _session_row()
    _set_session_cookie(response, secret, row)
    headers = _set_cookie_headers(response)
    assert len(headers) == 1
    head, attrs = _cookie_attrs(headers[0])
    assert head == f"{settings.session_cookie_name}={secret}"
    assert settings.session_cookie_name == "samanvay_session"
    assert "httponly" in attrs
    assert attrs.get("samesite", "").lower() == "lax"
    assert attrs.get("path") == "/"
    assert "domain" not in attrs
    assert ("secure" in attrs) == settings.cookie_secure
    assert int(attrs["max-age"]) > 0

    # Clearing uses the identical attribute contract.
    clear = Response()
    _clear_session_cookie(clear)
    _, clear_attrs = _cookie_attrs(_set_cookie_headers(clear)[0])
    assert clear_attrs.get("max-age") == "0"
    assert clear_attrs.get("path") == "/"
    assert "httponly" in clear_attrs
    assert "domain" not in clear_attrs
    assert ("secure" in clear_attrs) == settings.cookie_secure


def test_set_session_cookie_uses_host_prefix_and_secure_in_production(monkeypatch):
    """__Host- prefix contract: Secure + Path=/ + no Domain, production only."""
    monkeypatch.setattr(settings, "app_env", "production")
    assert settings.session_cookie_name == "__Host-samanvay_session"
    assert settings.cookie_secure is True

    response = Response()
    secret = session_service.generate_session_secret()
    _set_session_cookie(response, secret, _session_row())
    head, attrs = _cookie_attrs(_set_cookie_headers(response)[0])
    assert head == f"__Host-samanvay_session={secret}"
    assert "secure" in attrs, "production session cookie must be Secure"
    assert attrs.get("path") == "/"
    assert "httponly" in attrs
    assert attrs.get("samesite", "").lower() == "lax"
    assert "domain" not in attrs

    clear = Response()
    _clear_session_cookie(clear)
    _, clear_attrs = _cookie_attrs(_set_cookie_headers(clear)[0])
    assert "secure" in clear_attrs
    assert clear_attrs.get("path") == "/"


def test_production_configuration_rejects_insecure_cookie():
    """A production deployment must fail closed on SESSION_COOKIE_SECURE=false."""
    with pytest.raises(ValidationError):
        Settings(app_env="production", session_cookie_secure=False)



# ── Telemetry staging stays sanitized ────────────────────────────────────────

class _RecordingDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)


def test_record_security_event_stages_sanitized_copy():
    """Event metadata is copied; callers cannot later inject or leak secrets."""
    db = _RecordingDB()
    metadata = {"reason": "session_unknown"}
    event = session_service.record_security_event(
        db,
        session_service.EVENT_LOGIN_FAILURE,
        user_id=7,
        session_id="11111111-1111-1111-1111-111111111111",
        success=False,
        user_agent="U" * 600,  # must be truncated to the 512-char column
        metadata=metadata,
    )
    metadata["reason"] = "mutated-after-the-fact"
    assert db.added == [event]
    assert event.event_type == "LOGIN_FAILURE"
    assert event.success is False
    assert event.user_id == 7
    assert event.event_metadata == {"reason": "session_unknown"}
    assert len(event.user_agent) == 512


def test_invalid_session_attempt_event_carries_no_secret_material():
    """record_invalid_session_attempt never receives the raw secret or its hash."""
    secret = session_service.generate_session_secret()
    digest = session_service.hash_session_secret(secret)
    row = _session_row(revoked=True)

    db = _RecordingDB()
    db.commit = lambda: None  # no persistent storage in this unit boundary
    session_service.record_invalid_session_attempt(
        db, outcome="revoked", session=row, ip_address="127.0.0.1"
    )
    event = db.added[0]
    assert event.event_type == "LOGIN_FAILURE"
    assert event.success is False
    assert event.user_id == row.user_id
    assert event.session_id == row.id
    assert event.event_metadata == {"reason": "session_revoked"}
    serialized = repr(event.event_metadata) + repr(event.user_agent) + repr(event.ip_address)
    assert secret not in serialized
    assert digest not in serialized

    assert session_service.hash_session_secret("garbage!!") is None
    assert session_service.hash_session_secret("too-short") is None
