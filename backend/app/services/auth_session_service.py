"""
AUTH-005 / AUTH-006 server-side authentication session lifecycle.

Responsibilities:
  * generate the browser session secret (256-bit CSPRNG, unpadded base64url)
  * hash the raw secret (SHA-256, lowercase 64-char hex) for storage/lookup
  * create, resolve, touch and revoke ``AuthSession`` records
  * emit authoritative ``SecurityEvent`` telemetry

Frozen rules enforced here:
  * the raw browser session secret is NEVER stored or logged
  * ``auth_sessions.session_token_hash`` stores only the SHA-256 digest
  * session creation + SESSION_CREATED + LOGIN_SUCCESS commit in one transaction
  * logout revocation + SESSION_REVOKED + LOGOUT commit in one transaction
"""

import base64
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.tables import AuthSession, SecurityEvent, User

SESSION_SECRET_BYTES = 32

# Authoritative AUTH-006 authentication/security telemetry event types.
EVENT_LOGIN_SUCCESS = "LOGIN_SUCCESS"
EVENT_LOGIN_FAILURE = "LOGIN_FAILURE"
EVENT_SESSION_CREATED = "SESSION_CREATED"
EVENT_SESSION_REVOKED = "SESSION_REVOKED"
EVENT_LOGOUT = "LOGOUT"
EVENT_AUTHORIZATION_FAILURE = "AUTHORIZATION_FAILURE"
EVENT_RATE_LIMIT_TRIGGERED = "RATE_LIMIT_TRIGGERED"
EVENT_ACCOUNT_APPROVED = "ACCOUNT_APPROVED"
EVENT_ACCOUNT_REJECTED = "ACCOUNT_REJECTED"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_session_secret() -> str:
    """Return a fresh 256-bit CSPRNG secret as unpadded base64url text."""
    return (
        base64.urlsafe_b64encode(secrets.token_bytes(SESSION_SECRET_BYTES))
        .rstrip(b"=")
        .decode("ascii")
    )


def decode_session_secret(secret: Optional[str]) -> Optional[bytes]:
    """Strictly decode a canonical unpadded-base64url session secret to 32 bytes."""
    if not secret or not isinstance(secret, str):
        return None
    try:
        raw = base64.urlsafe_b64decode(secret + "=" * (-len(secret) % 4))
    except Exception:
        return None
    if len(raw) != SESSION_SECRET_BYTES:
        return None
    # Reject non-canonical encodings (padding, non-urlsafe alphabet).
    if base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii") != secret:
        return None
    return raw


def hash_session_secret(secret: Optional[str]) -> Optional[str]:
    """Return the lowercase 64-char hex SHA-256 digest of the raw secret bytes."""
    raw = decode_session_secret(secret)
    if raw is None:
        return None
    return hashlib.sha256(raw).hexdigest()


def _sanitize_metadata(metadata: Optional[Mapping[str, Any]]) -> dict:
    """Copy non-secret event metadata. Callers must never pass secrets here."""
    if not metadata:
        return {}
    return {str(k): v for k, v in metadata.items()}


def record_security_event(
    db: Session,
    event_type: str,
    *,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    success: bool = True,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> SecurityEvent:
    """Stage a ``SecurityEvent`` on the current transaction (no commit)."""
    event = SecurityEvent(
        id=str(uuid.uuid4()),
        event_type=event_type,
        user_id=user_id,
        session_id=session_id,
        created_at=_utcnow(),
        success=bool(success),
        ip_address=(ip_address or None),
        user_agent=(user_agent or None)[:512] if user_agent else None,
        event_metadata=_sanitize_metadata(metadata),
    )
    db.add(event)
    return event


def create_session(
    db: Session,
    user: User,
    *,
    ttl_minutes: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[str, AuthSession]:
    """Stage a new ``AuthSession`` (+ SESSION_CREATED event). Does not commit."""
    now = _utcnow()
    expires_at = now + timedelta(
        minutes=ttl_minutes or settings.session_absolute_expire_minutes
    )
    secret = generate_session_secret()
    token_hash = hash_session_secret(secret)
    if token_hash is None:  # defensive: CSPRNG failure must fail closed
        raise RuntimeError("Failed to generate a valid session secret")

    session = AuthSession(
        id=str(uuid.uuid4()),
        session_token_hash=token_hash,
        user_id=user.id,
        created_at=now,
        last_seen_at=now,
        expires_at=expires_at,
        revoked_at=None,
        ip_address=(ip_address or None),
        user_agent=(user_agent or None)[:512] if user_agent else None,
    )
    db.add(session)
    db.flush()
    record_security_event(
        db,
        EVENT_SESSION_CREATED,
        user_id=user.id,
        session_id=session.id,
        success=True,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return secret, session


def establish_login_session(
    db: Session,
    user: User,
    *,
    ttl_minutes: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[str, AuthSession]:
    """Create the session and commit it with SESSION_CREATED + LOGIN_SUCCESS atomically."""
    secret, session = create_session(
        db,
        user,
        ttl_minutes=ttl_minutes,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    record_security_event(
        db,
        EVENT_LOGIN_SUCCESS,
        user_id=user.id,
        session_id=session.id,
        success=True,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(session)
    return secret, session


def record_login_failure(
    db: Session,
    *,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    """Record a LOGIN_FAILURE event. Anonymous events use user_id = NULL."""
    record_security_event(
        db,
        EVENT_LOGIN_FAILURE,
        user_id=user_id,
        session_id=None,
        success=False,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={"reason": reason} if reason else None,
    )
    try:
        db.commit()
    except Exception:
        # A failed telemetry write must not become a successful authentication.
        db.rollback()


def resolve_session(db: Session, secret: Optional[str]) -> Optional[AuthSession]:
    """Resolve a live (non-revoked, non-expired) session by cookie-secret hash."""
    token_hash = hash_session_secret(secret)
    if token_hash is None:
        return None
    session = (
        db.query(AuthSession)
        .filter(AuthSession.session_token_hash == token_hash)
        .first()
    )
    if session is None or session.revoked_at is not None:
        return None
    expires_at = session.expires_at
    if expires_at is None:
        return None
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if _utcnow() >= expires_at:
        return None
    return session


def touch_session(db: Session, session: AuthSession) -> None:
    """Update ``last_seen_at`` and commit (account state is rechecked per request)."""
    session.last_seen_at = _utcnow()
    db.commit()


def revoke_session_for_logout(
    db: Session,
    session: AuthSession,
    *,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Set revoked_at and commit revocation + SESSION_REVOKED + LOGOUT atomically."""
    if session.revoked_at is not None:
        return  # idempotent: never emit duplicate revocation/logout events
    session.revoked_at = _utcnow()
    record_security_event(
        db,
        EVENT_SESSION_REVOKED,
        user_id=session.user_id,
        session_id=session.id,
        success=True,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    record_security_event(
        db,
        EVENT_LOGOUT,
        user_id=session.user_id,
        session_id=session.id,
        success=True,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise