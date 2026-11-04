"""
AUTH-006 Section 8 abuse-control interface.

A product-neutral rate-limit interface is required. Production thresholds and the
shared provider remain deployment/security-policy configuration and are NOT
selected here. The in-memory guard is a per-process development/test default that
fails closed; a shared provider must be injected for multi-process deployment.
"""

import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Protocol


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0
    reason_code: str = ""


class RateLimitGuard(Protocol):
    def consume(self, scope: str, subject: str, *, cost: int = 1) -> RateLimitDecision:
        """Consume ``cost`` units for ``subject`` within ``scope``."""


class InMemoryRateLimitGuard:
    """Per-process fixed-window guard (development/test default).

    Fails closed: any internal error denies the request.
    """

    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = max(1, int(limit))
        self._window = max(1, int(window_seconds))
        self._buckets: Dict[str, tuple] = {}
        self._lock = threading.Lock()

    def consume(self, scope: str, subject: str, *, cost: int = 1) -> RateLimitDecision:
        try:
            now = time.monotonic()
            key = f"{scope}:{subject}"
            with self._lock:
                window_start, count = self._buckets.get(key, (now, 0))
                if now - window_start >= self._window:
                    window_start, count = now, 0
                count += max(1, int(cost))
                self._buckets[key] = (window_start, count)
                if count > self._limit:
                    retry = int(self._window - (now - window_start)) + 1
                    return RateLimitDecision(False, retry, "RATE_LIMIT_EXCEEDED")
            return RateLimitDecision(True)
        except Exception:
            # Fail closed for authentication abuse surfaces.
            return RateLimitDecision(False, 1, "RATE_LIMIT_BACKEND_FAILURE")


_guards: Dict[str, RateLimitGuard] = {}
_guard_lock = threading.Lock()


def get_rate_limit_guard(
    scope: str, *, limit: int = 30, window_seconds: int = 60
) -> RateLimitGuard:
    """Return the process-local guard for a scope.

    Deployment must replace this with a shared provider before multi-process
    rollout. Thresholds here are development/test placeholders only.
    """
    with _guard_lock:
        guard = _guards.get(scope)
        if guard is None:
            guard = InMemoryRateLimitGuard(limit=limit, window_seconds=window_seconds)
            _guards[scope] = guard
        return guard