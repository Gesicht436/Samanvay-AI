"""Task 23 — InMemoryRateLimitGuard unit tests (no database required).

Exercises the real ``backend/app/services/auth_rate_limit.py``
implementation through its existing public interface:

* boundary: the configured number of attempts is allowed; the next is denied
* fixed-window reset via a mocked monotonic clock (no sleeping)
* independent scopes/subjects have independent budgets
* Retry-After is positive and bounded by the configured window
* internal limiter failure denies the request (fail-closed)

DB-backed acceptance (429 over HTTP on ``POST /auth/login``) remains
BLOCKED while PostgreSQL is unavailable — Runbook sections 4, 16, 22.
"""

import pytest
from pydantic import ValidationError

from backend.app.core.config import Settings
from backend.app.services import auth_rate_limit as rate_limit
from backend.app.services.auth_rate_limit import InMemoryRateLimitGuard


def test_allows_configured_attempts_then_denies(monkeypatch):
    """Boundary: ``limit`` attempts allowed; attempt ``limit + 1`` denied."""
    now = [1000.0]
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: now[0])
    guard = InMemoryRateLimitGuard(limit=10, window_seconds=60)

    for _ in range(10):
        decision = guard.consume("login", "engineer_oil")
        assert decision.allowed is True

    denied = guard.consume("login", "engineer_oil")
    assert denied.allowed is False
    assert denied.reason_code == "RATE_LIMIT_EXCEEDED"


def test_fixed_window_resets_after_expiry(monkeypatch):
    """A new fixed window restores the full budget (mocked clock)."""
    now = [2000.0]
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: now[0])
    guard = InMemoryRateLimitGuard(limit=3, window_seconds=60)

    for _ in range(3):
        assert guard.consume("login", "stores_ongc").allowed is True
    assert guard.consume("login", "stores_ongc").allowed is False

    now[0] += 60  # window boundary: now - window_start >= window
    assert guard.consume("login", "stores_ongc").allowed is True


def test_independent_scopes_and_subjects_have_independent_budgets(monkeypatch):
    """Budget is keyed per scope:subject; exhaustion does not leak across keys."""
    now = [3000.0]
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: now[0])
    guard = InMemoryRateLimitGuard(limit=2, window_seconds=60)

    assert guard.consume("login", "user_a").allowed is True
    assert guard.consume("login", "user_a").allowed is True
    assert guard.consume("login", "user_a").allowed is False

    # A different subject in the same scope is unaffected.
    assert guard.consume("login", "user_b").allowed is True
    # A different scope for the same subject is unaffected.
    assert guard.consume("other", "user_a").allowed is True


def test_retry_after_is_positive_and_bounded_by_window(monkeypatch):
    """Denied decisions carry 1 <= retry_after_seconds <= window_seconds."""
    now = [4000.0]
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: now[0])
    window = 60
    guard = InMemoryRateLimitGuard(limit=1, window_seconds=window)

    assert guard.consume("login", "admin").allowed is True

    now[0] += 7  # partway through the window
    denied = guard.consume("login", "admin")
    assert denied.allowed is False
    assert 1 <= denied.retry_after_seconds <= window


def test_login_rate_limit_settings_defaults_and_validation():
    """Configured login thresholds default to 10 attempts / 60 seconds.

    Nonsensical values (below 1) are rejected, consistent with the project's
    existing ``Field(ge=...)`` validation patterns.
    """
    defaults = Settings()
    assert defaults.auth_login_rate_limit_attempts == 10
    assert defaults.auth_login_rate_limit_window_seconds == 60

    custom = Settings(
        auth_login_rate_limit_attempts=5,
        auth_login_rate_limit_window_seconds=30,
    )
    assert custom.auth_login_rate_limit_attempts == 5
    assert custom.auth_login_rate_limit_window_seconds == 30

    with pytest.raises(ValidationError):
        Settings(auth_login_rate_limit_attempts=0)
    with pytest.raises(ValidationError):
        Settings(auth_login_rate_limit_window_seconds=0)


@pytest.mark.parametrize("broken_attr", ["_buckets", "_lock"])
def test_internal_failure_denies_request_fail_closed(broken_attr):
    """Any internal limiter error denies the request (fail-closed)."""
    guard = InMemoryRateLimitGuard(limit=10, window_seconds=60)
    setattr(guard, broken_attr, None)  # force an AttributeError inside consume

    decision = guard.consume("login", "engineer_oil")
    assert decision.allowed is False
    assert decision.reason_code == "RATE_LIMIT_BACKEND_FAILURE"
