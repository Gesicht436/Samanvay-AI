"""
AUTH-006 Section 4 CSRF primitives.

Frozen model: a *session-bound synchronizer token* combined with strict Origin
validation. The token is derived deterministically from the stored
session-secret hash and is never persisted in the database.

    HMAC-SHA256(key = session-secret-derived material, message = "samanvay-csrf-v1")

The key material is the lowercase hexadecimal SHA-256 session-token hash that
is already stored server-side, so no additional secret is stored or logged.
"""

import hashlib
import hmac
from typing import Iterable, Optional, Sequence

CSRF_MESSAGE = b"samanvay-csrf-v1"


def derive_csrf_token(session_token_hash: str) -> str:
    """Derive the deterministic session-bound CSRF token (lowercase hex)."""
    key = bytes.fromhex(session_token_hash)
    return hmac.new(key, CSRF_MESSAGE, hashlib.sha256).hexdigest()


def verify_csrf_token(session_token_hash: str, presented: Optional[str]) -> bool:
    """Constant-time comparison of a presented CSRF token against the derived token."""
    if not presented or not isinstance(presented, str):
        return False
    try:
        expected = derive_csrf_token(session_token_hash)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(expected, presented.strip())


def normalize_origin(origin: Optional[str]) -> Optional[str]:
    """Normalize an Origin header for exact comparison (drop trailing slash)."""
    if not origin or not isinstance(origin, str):
        return None
    return origin.strip().rstrip("/")


def origin_allowed(origin: Optional[str], allowed_origins: Iterable[str]) -> bool:
    """Return True only when the request Origin exactly matches the allowlist.

    A missing or malformed Origin is never allowed. The allowlist is an explicit
    configured set; untrusted Host / X-Forwarded-Host headers are never consulted.
    """
    normalized = normalize_origin(origin)
    if not normalized:
        return False
    allowed = {o.rstrip("/") for o in allowed_origins if o}
    return normalized in allowed