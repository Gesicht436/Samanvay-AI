"""FastAPI dependency providers for authentication and authorization.

AUTH-006 target flow:

    get_db_session
        -> get_current_session   (cookie -> hash -> session lookup)
        -> get_current_user      (user + is_active + is_approved + last_seen_at)
        -> require_permission(...) (centralized AUTH-007 policy)
        -> service -> repository

Authentication is cookie-session based only: there is no bearer/JWT fallback.
A malformed, unknown, expired, revoked, inactive or unapproved presented
credential fails closed (401) and never silently becomes anonymous.
Client-controlled fields (including ``X-CPSE-ID``) never establish authorization.
"""

from fastapi import Request, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Generator, Tuple
from datetime import datetime, timezone

from backend.app.models.base import get_db
from backend.app.models.tables import IdempotencyKey, User, AuthSession
from backend.app.core.config import settings
from backend.app.core import csrf as csrf_core
from backend.app.core.authorization import (
    ALLOW,
    Action,
    AuthorizationContext,
    AuthorizationRequest,
    Resource,
    build_subject,
    evaluate,
)
from backend.app.services import auth_session_service as session_service


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


def _client_meta(request: Request) -> Tuple[Optional[str], Optional[str]]:
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip, user_agent


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _invalid_session_unauthorized() -> HTTPException:
    """401 for a presented-but-invalid session, clearing the dead cookie.

    AUTH-006 Section 12 requires ``401; clear cookie`` for malformed, unknown,
    expired or revoked presented sessions (a merely *missing* cookie is a plain
    401 with no cookie to clear).
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid, expired, or revoked session.",
        headers={"set-cookie": session_service.session_cookie_deletion_header()},
    )


def get_current_session(
    request: Request,
    db: Session = Depends(get_db_session),
) -> AuthSession:
    """Resolve the presented session cookie to a live ``AuthSession``, or 401.

    There is no ``Authorization``/Bearer fallback. A missing cookie, or a
    malformed, unknown, expired or revoked session, fails closed. A presented
    cookie that resolves to no live session also clears the dead cookie and
    records sanitized ``LOGIN_FAILURE`` telemetry (never the raw secret).
    """
    raw = request.cookies.get(settings.session_cookie_name)
    if not raw:
        raise _unauthorized("Authentication required. Provide a valid session cookie.")
    session, outcome = session_service.resolve_session_with_outcome(db, raw)
    if outcome != "live":
        ip, user_agent = _client_meta(request)
        session_service.record_invalid_session_attempt(
            db, outcome=outcome, session=session, ip_address=ip, user_agent=user_agent
        )
        raise _invalid_session_unauthorized()
    return session


def get_current_user(
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db_session),
) -> User:
    """Load the account and enforce active + approved state on every request."""
    user = db.query(User).filter(User.id == session.user_id).first()
    if user is None or not user.is_active or not user.is_approved:
        raise _unauthorized("Authentication required.")
    session_service.touch_session(db, session)
    return user


def _record_authorization_failure(db: Session, current_user: User, permission: str, reason_code: str) -> None:
    try:
        session_service.record_security_event(
            db,
            session_service.EVENT_AUTHORIZATION_FAILURE,
            user_id=current_user.id,
            success=False,
            metadata={"permission": permission, "reason": reason_code},
        )
        db.commit()
    except Exception:
        db.rollback()


def require_permission(permission: str, resource_type: Optional[str] = None):
    """Centralized AUTH-007 authorization dependency. Fails closed with 403."""

    def checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db_session),
    ) -> User:
        ip, _ua = _client_meta(request)
        decision = evaluate(
            AuthorizationRequest(
                subject=build_subject(current_user),
                action=Action(permission=permission),
                resource=Resource(resource_type=resource_type),
                context=AuthorizationContext(
                    request_id=request.headers.get("x-request-id"),
                    ip_address=ip,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ),
            )
        )
        if decision.decision != ALLOW:
            _record_authorization_failure(db, current_user, permission, decision.reason_code)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "AUTHORIZATION_DENIED", "reason": decision.reason_code},
            )
        return current_user

    return checker


def require_any_permission(*permissions: str, resource_type: Optional[str] = None):
    """Canonical AUTH-007 gate for a route guarded by more than one permission.

    Identical evaluation, fail-closed behaviour, security-event recording and 403
    contract as ``require_permission``; it only allows the request when the
    centralized policy grants **any one** of the supplied frozen permissions.

    This grants no permission of its own and adds no role grant: a caller must
    still hold one of ``permissions`` through the frozen AUTH-007 mapping, so a
    role absent from AUTH-007 (including SUPER_ADMIN) can never pass.
    """
    if not permissions:
        raise ValueError("require_any_permission requires at least one permission")

    def checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db_session),
    ) -> User:
        ip, _ua = _client_meta(request)
        subject = build_subject(current_user)
        context = AuthorizationContext(
            request_id=request.headers.get("x-request-id"),
            ip_address=ip,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        for permission in permissions:
            decision = evaluate(
                AuthorizationRequest(
                    subject=subject,
                    action=Action(permission=permission),
                    resource=Resource(resource_type=resource_type),
                    context=context,
                )
            )
            if decision.decision == ALLOW:
                return current_user
            last_reason_code = decision.reason_code
        _record_authorization_failure(
            db, current_user, ",".join(permissions), last_reason_code
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "AUTHORIZATION_DENIED",
                "reason": last_reason_code,
                "required_any_of": list(permissions),
            },
        )

    return checker


def require_csrf(
    request: Request,
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db_session),
) -> AuthSession:
    """AUTH-006 Section 4: strict Origin allowlist + session-bound CSRF token.

    Returns 403 before any mutation when either check fails.
    """
    if not csrf_core.origin_allowed(request.headers.get("origin"), settings.allowed_origins_list):
        user = db.query(User).filter(User.id == session.user_id).first()
        if user is not None:
            _record_authorization_failure(
                db,
                user,
                permission="CSRF_ORIGIN",
                reason_code="CSRF_ORIGIN_DENIED",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "CSRF_ORIGIN_DENIED"},
        )
    if not csrf_core.verify_csrf_token(
        session.session_token_hash, request.headers.get("x-csrf-token")
    ):
        user = db.query(User).filter(User.id == session.user_id).first()
        if user is not None:
            _record_authorization_failure(
                db,
                user,
                permission="CSRF_TOKEN",
                reason_code="CSRF_TOKEN_DENIED",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "CSRF_TOKEN_DENIED"},
        )
    return session


def validate_idempotency_key(
    request: Request,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db_session),
):
    """
    Validates API idempotency for high-value asset transfers and requisitions.
    If already completed and not expired, returns cached response.
    """
    if not idempotency_key:
        return None

    key_record = db.query(IdempotencyKey).filter(IdempotencyKey.key == idempotency_key).first()
    if key_record:
        now = datetime.now(timezone.utc)
        # Handle timezone-aware and naive datetime comparison safely
        expires = key_record.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if now < expires:
            return {"status": "CACHED", "data": key_record.response_body}

    return idempotency_key


def verify_cpse_access(
    current_user: User = Depends(get_current_user),
) -> str:
    """Return the caller's CPSE derived ONLY from the authenticated session.

    ``X-CPSE-ID`` and other client-supplied fields never establish tenant
    authority (AUTH-003 / AUTH-007 CPSE isolation).
    """
    return current_user.cpse


def require_roles(allowed_roles: List[str]):
    """
    Legacy role-based compatibility dependency.

    Uses the current session-based authentication flow. This exists only
    for routes that have not yet migrated to the canonical AUTH-007
    permission dependency.
    """
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions",
            )
        return current_user

    return role_checker


class PaginationParams:
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = skip
        self.limit = limit


class InventoryFilterParams:
    def __init__(
        self,
        cpse: Optional[str] = None,
        depot: Optional[str] = None,
        status: Optional[str] = None,
        item_type: Optional[str] = None,
    ):
        self.cpse = cpse
        self.depot = depot
        self.status = status
        self.item_type = item_type
