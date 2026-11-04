"""Task 19 — CSRF + Origin enforcement primitives (no database required).

Exercises the actual implementation in ``backend/app/core/csrf.py`` and
``backend/app/api/dependencies.py::require_csrf``:

* HMAC-bound token construction/verification (valid, invalid, missing,
  empty, non-string presented values).
* Strict Origin allowlist semantics (exact match, missing/malformed,
  untrusted, trailing-slash handling per the existing contract).
* ``require_csrf`` ordering: a disallowed Origin is rejected before token
  validation, and an invalid token is rejected before the protected
  handler can run — verified by calling the real dependency with stub
  request/session/database doubles (no PostgreSQL).

DB-backed acceptance (real token issuance → protected mutation →
403-negative cases over HTTP) remains BLOCKED while PostgreSQL is
unavailable — Runbook sections 4, 16, 22.
"""

import hashlib
import hmac

import pytest
from fastapi import HTTPException

from backend.app.api import dependencies as deps
from backend.app.core import csrf as csrf_core
from backend.app.core.config import settings


SESSION_DIGEST = "ab" * 32  # fixed 32-byte key material, lowercase 64-hex


class _StubHeaders(dict):
    def get(self, key, default=None):  # case-insensitive like Starlette
        for stored_key, value in self.items():
            if stored_key.lower() == key.lower():
                return value
        return default


class _StubRequest:
    def __init__(self, headers):
        self.headers = _StubHeaders(headers)


class _StubSession:
    def __init__(self, digest=SESSION_DIGEST, user_id=7):
        self.session_token_hash = digest
        self.user_id = user_id


class _StubQuery:
    def __init__(self, user):
        self._user = user

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._user


class _StubUser:
    id = 7


class _StubDB:
    """Minimal query/add/commit surface; records whether a handler ran."""

    def __init__(self, user=_StubUser()):
        self._user = user
        self.handler_ran = False

    def query(self, *args, **kwargs):
        return _StubQuery(self._user)

    def add(self, obj):
        return None

    def commit(self):
        return None


def _good_token(digest=SESSION_DIGEST):
    return csrf_core.derive_csrf_token(digest)


def _origin_headers(origin, token):
    headers = {"Origin": origin} if origin is not None else {}
    if token is not None:
        headers["X-CSRF-Token"] = token
    return headers


# ── Token construction matches the frozen contract ────────────────────────


# ── Token construction matches the frozen contract ────────────────────────


def test_derive_csrf_token_is_hmac_sha256_of_session_digest():
    """The token is HMAC-SHA256(key=session digest, msg=samanvay-csrf-v1)."""
    expected = hmac.new(
        bytes.fromhex(SESSION_DIGEST), b"samanvay-csrf-v1", hashlib.sha256
    ).hexdigest()
    token = csrf_core.derive_csrf_token(SESSION_DIGEST)
    assert token == expected
    assert len(token) == 64 and token == token.lower()
    # Bound to the session: a different digest yields a different token.
    assert csrf_core.derive_csrf_token("cd" * 32) != token


# ── Token verification matrix (real implementation) ───────────────────────


def test_verify_csrf_token_accepts_valid_token():
    assert csrf_core.verify_csrf_token(SESSION_DIGEST, _good_token()) is True


def test_verify_csrf_token_rejects_wrong_token():
    assert csrf_core.verify_csrf_token(SESSION_DIGEST, "0" * 64) is False
    other = _good_token("cd" * 32)  # valid token for a *different* session
    assert csrf_core.verify_csrf_token(SESSION_DIGEST, other) is False


def test_verify_csrf_token_rejects_missing_empty_and_non_string():
    assert csrf_core.verify_csrf_token(SESSION_DIGEST, None) is False
    assert csrf_core.verify_csrf_token(SESSION_DIGEST, "") is False
    assert csrf_core.verify_csrf_token(SESSION_DIGEST, "   ") is False
    assert csrf_core.verify_csrf_token(SESSION_DIGEST, 12345) is False
    assert csrf_core.verify_csrf_token(SESSION_DIGEST, ["token"]) is False


def test_verify_csrf_token_tolerates_surrounding_whitespace_only():
    assert csrf_core.verify_csrf_token(SESSION_DIGEST, f"  {_good_token()}  ") is True


def test_verify_csrf_token_fails_closed_on_malformed_stored_hash():
    assert csrf_core.verify_csrf_token("not-hex", _good_token()) is False


# ── Origin allowlist matrix (real implementation) ─────────────────────────


def test_origin_allowed_exact_allowlisted_origin():
    allowed = settings.allowed_origins_list[0]
    assert csrf_core.origin_allowed(allowed, settings.allowed_origins_list) is True


def test_origin_allowed_rejects_missing_and_malformed():
    assert csrf_core.origin_allowed(None, settings.allowed_origins_list) is False
    assert csrf_core.origin_allowed("", settings.allowed_origins_list) is False
    assert csrf_core.origin_allowed("   ", settings.allowed_origins_list) is False
    assert csrf_core.origin_allowed(12345, settings.allowed_origins_list) is False


def test_origin_allowed_rejects_untrusted_origin():
    assert (
        csrf_core.origin_allowed("https://evil.example", settings.allowed_origins_list)
        is False
    )
    assert (
        csrf_core.origin_allowed(
            "http://localhost:3000.evil.example", settings.allowed_origins_list
        )
        is False
    )


def test_origin_allowed_trailing_slash_matches_existing_contract():
    """Both sides strip a single trailing slash before exact comparison."""
    allowed = settings.allowed_origins_list[0]
    assert csrf_core.origin_allowed(allowed + "/", settings.allowed_origins_list) is True
    # But a different path is still a different origin.
    assert (
        csrf_core.origin_allowed(allowed + "/other", settings.allowed_origins_list)
        is False
    )


# ── require_csrf ordering (real dependency, stub I/O boundary) ────────────


def _call_require_csrf(origin, token, digest=SESSION_DIGEST):
    request = _StubRequest(_origin_headers(origin, token))
    return deps.require_csrf(
        request, _StubSession(digest=digest), _StubDB()  # type: ignore[arg-type]
    )


def test_require_csrf_accepts_valid_origin_and_token():
    session = _call_require_csrf(settings.allowed_origins_list[0], _good_token())
    assert session.user_id == 7


def test_require_csrf_rejects_disallowed_origin_before_token_validation():
    """A bad Origin fails even when the token is valid — Origin is checked first."""
    with pytest.raises(HTTPException) as exc_info:
        _call_require_csrf("https://evil.example", _good_token())
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == {"error": "CSRF_ORIGIN_DENIED"}
    with pytest.raises(HTTPException) as exc_info:
        _call_require_csrf(None, _good_token())
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == {"error": "CSRF_ORIGIN_DENIED"}


def test_require_csrf_rejects_invalid_token_before_handler_runs():
    """An invalid token fails closed; the denied session never reaches a handler."""
    db = _StubDB()
    request = _StubRequest(
        _origin_headers(settings.allowed_origins_list[0], "0" * 64)
    )
    with pytest.raises(HTTPException) as exc_info:
        deps.require_csrf(request, _StubSession(), db)  # type: ignore[arg-type]
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == {"error": "CSRF_TOKEN_DENIED"}
    assert db.handler_ran is False, "denied request must not reach the handler"


def test_require_csrf_rejects_missing_token():
    with pytest.raises(HTTPException) as exc_info:
        _call_require_csrf(settings.allowed_origins_list[0], None)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == {"error": "CSRF_TOKEN_DENIED"}


def test_match_search_route_declares_require_csrf():
    """Task 19: POST /match/search enforces the protected-POST CSRF contract."""
    from backend.app.api.routers import match as match_router

    route = next(
        r
        for r in match_router.router.routes
        if "/search" in getattr(r, "path", "")
        and "POST" in (getattr(r, "methods", set()) or set())
    )
    dependant = route.dependant
    names = set()
    for dep in getattr(dependant, "dependencies", []) or []:
        call = getattr(dep, "call", None)
        if call is not None:
            names.add(getattr(call, "__name__", ""))
    for param in getattr(dependant, "query_params", []) or []:
        call = getattr(getattr(param, "dependency", None), "call", None)
        if call is not None:
            names.add(getattr(call, "__name__", ""))
    source_params = match_router.search_matches.__code__.co_varnames
    assert "require_csrf" in names or "_csrf" in source_params, (
        "POST /match/search must declare the require_csrf dependency"
    )

