"""
Authentication API router (AUTH-006).

Cookie-session based authentication only. No JWT, refresh token, access token or
bearer token is issued or accepted.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import (
    _record_authorization_failure,
    get_current_session,
    get_current_user,
    get_db_session,
    require_csrf,
    require_permission,
)
from backend.app.core import csrf as csrf_core
from backend.app.core import permissions as perm
from backend.app.core.config import settings
from backend.app.core.security import (
    get_password_hash,
    verify_password,
    verify_password_dummy,
)
from backend.app.models.tables import AuthSession, User
from backend.app.schemas.auth import (
    CsrfTokenResponse,
    SEED_USERS,
    UserLogin,
    UserProvisionRequest,
    UserResponse,
)
from backend.app.services import auth_rate_limit as rate_limit
from backend.app.services import auth_session_service as session_service
from backend.app.services import hibp_service

logger = logging.getLogger("samanvay.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _client_meta(request: Request):
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip, user_agent


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _set_session_cookie(response: Response, secret: str, session: AuthSession) -> None:
    """Set the Secure/HttpOnly/SameSite=Lax host-only session cookie."""
    expires_at = _as_utc(session.expires_at)
    max_age = max(0, int((expires_at - datetime.now(timezone.utc)).total_seconds()))
    response.set_cookie(
        key=settings.session_cookie_name,
        value=secret,
        max_age=max_age,
        expires=expires_at,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        cpse=user.cpse,
        depot_id=user.depot_id,
        is_active=user.is_active,
        is_approved=user.is_approved,
    )


@router.post(
    "/login",
    response_model=UserResponse,
    summary="Authenticate credentials and establish a server-side session",
)
def login_user(
    credentials: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db_session),
):
    """Authenticate an account and establish a revocable server-side session.

    Returns public user data only. No JWT/access/refresh/session secret is returned.
    """
    ip, user_agent = _client_meta(request)

    guard = rate_limit.get_rate_limit_guard(
        "login",
        limit=settings.auth_login_rate_limit_attempts,
        window_seconds=settings.auth_login_rate_limit_window_seconds,
    )
    rl = guard.consume("login", credentials.username.strip().lower())
    if not rl.allowed:
        session_service.record_security_event(
            db,
            session_service.EVENT_RATE_LIMIT_TRIGGERED,
            success=False,
            ip_address=ip,
            user_agent=user_agent,
            metadata={"scope": "login"},
        )
        try:
            db.commit()
        except Exception:
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please retry later.",
            headers={"Retry-After": str(rl.retry_after_seconds or 60)},
        )

    user = db.query(User).filter(User.username == credentials.username.strip()).first()

    if user is None:
        verify_password_dummy(credentials.password)  # timing equalization
        session_service.record_login_failure(
            db, ip_address=ip, user_agent=user_agent, reason="unknown_user"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not verify_password(credentials.password, user.hashed_password):
        session_service.record_login_failure(
            db, user_id=user.id, ip_address=ip, user_agent=user_agent, reason="bad_password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active or not user.is_approved:
        session_service.record_login_failure(
            db, user_id=user.id, ip_address=ip, user_agent=user_agent, reason="account_state"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    try:
        secret, session = session_service.establish_login_session(
            db, user, ip_address=ip, user_agent=user_agent
        )
    except Exception:
        logger.exception("Session persistence failure during login")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication temporarily unavailable. Please retry.",
        )

    _set_session_cookie(response, secret, session)
    return _user_response(user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current server-side session",
)
def logout_user(
    request: Request,
    db: Session = Depends(get_db_session),
):
    """Revoke the caller's session (AUTH-006 Section 2 logout flow).

    Origin validation always applies. A live session additionally requires the
    session-bound synchronizer token and is revoked atomically with its
    ``SESSION_REVOKED`` + ``LOGOUT`` telemetry (503 on persistence failure
    rather than a false success). An absent, malformed, unknown, expired or
    already-revoked session is an idempotent no-op: 204 after Origin
    validation, cookie cleared, and no duplicate revocation/logout events.
    """
    ip, user_agent = _client_meta(request)

    # 1. Origin allowlist validation — always the first gate for logout.
    if not csrf_core.origin_allowed(
        request.headers.get("origin"), settings.allowed_origins_list
    ):
        raw = request.cookies.get(settings.session_cookie_name)
        live = session_service.resolve_session(db, raw) if raw else None
        if live is not None:
            user = db.query(User).filter(User.id == live.user_id).first()
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

    # 2. Resolve the presented session cookie (hash lookup; never a token).
    raw = request.cookies.get(settings.session_cookie_name)
    session = session_service.resolve_session(db, raw) if raw else None
    if session is None:
        # Idempotent logout: there is no live session to revoke, so no
        # SESSION_REVOKED/LOGOUT events are emitted (no duplicates) and the
        # dead/absent cookie is cleared.
        resp = Response(status_code=status.HTTP_204_NO_CONTENT)
        _clear_session_cookie(resp)
        return resp

    # 3. Live session: session-bound synchronizer token required.
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

    # 4. Revoke + telemetry atomically; clear the cookie only after success.
    try:
        session_service.revoke_session_for_logout(
            db, session, ip_address=ip, user_agent=user_agent
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Logout could not be completed. Please retry.",
        )
    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_session_cookie(resp)
    return resp


@router.get(
    "/csrf",
    response_model=CsrfTokenResponse,
    summary="Obtain the session-bound CSRF token (not persisted)",
)
def get_csrf_token(
    response: Response,
    session: AuthSession = Depends(get_current_session),
):
    """Derive and return the session-bound synchronizer CSRF token."""
    response.headers["Cache-Control"] = "no-store"
    return CsrfTokenResponse(
        csrf_token=csrf_core.derive_csrf_token(session.session_token_hash)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Fetch current authenticated user profile and tenant claims",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Return the server-derived identity for the authenticated session."""
    return _user_response(current_user)


@router.get(
    "/seed-users",
    summary="List default seed persona accounts (development/test only)",
)
def get_seed_users():
    """Development/test only. Not available in production deployments.

    Strictly read-only: the persona list is served from the static seed
    definition. It performs no database access or mutation, creates no session
    and never discloses a seed credential.
    """
    if settings.is_production:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {
        "users": [user.model_dump() for user in SEED_USERS],
    }


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all users (centralized authorization: SYSTEM_ADMIN)",
)
def get_all_users(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission(perm.SYSTEM_ADMIN)),
):
    """Administrative account listing via centralized authorization policy."""
    return db.query(User).all()


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision an account (SUPER_ADMIN; active + unapproved, no session)",
)
def provision_user(
    payload: UserProvisionRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission(perm.ACCOUNT_PROVISION)),
    _csrf: AuthSession = Depends(require_csrf),
):
    """Account provisioning (AUTH-006). Creates an active but UNAPPROVED account.

    No session is created; approval is a separate administrative operation.
    ACCOUNT_PROVISIONED telemetry is committed atomically with the User INSERT
    (AUTH-5J.3, decision D-5J.3-1).
    """
    existing = (
        db.query(User)
        .filter(
            (User.username == payload.username.strip())
            | (User.email == payload.email.strip().lower())
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered.",
        )

    try:
        breach_count = hibp_service.check_password_against_hibp(payload.password)
    except hibp_service.HIBPVerificationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=hibp_service._RETRYABLE_VERIFICATION_MESSAGE,
            headers={"Retry-After": "300"},
        ) from None

    if breach_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=hibp_service._BREACHED_PASSWORD_MESSAGE,
        )

    # Server-side role validity gate (AUTH-006 §7): the Pydantic `UserRole`
    # enum constrains the request body, but this is an additive defense so that
    # a role outside the frozen `perm.VALID_ROLES` set can never be persisted
    # into `users.role`. The check runs before any `User` construction or DB
    # interaction and raises HTTP 422 otherwise.
    if payload.role.value not in perm.VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid role: the assigned role is not a valid sovereign functional role.",
        )

    user = User(
        username=payload.username.strip(),
        email=payload.email.strip().lower(),
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        role=payload.role.value if hasattr(payload.role, "value") else str(payload.role),
        cpse=payload.cpse.strip().upper(),
        depot_id=payload.depot_id.strip(),
        is_active=True,
        is_approved=False,
    )
    db.add(user)
    try:
        # AUTH-5J.3 (D-5J.3-1): flush assigns the target id, then stage
        # ACCOUNT_PROVISIONED on the same transaction so the User INSERT and
        # its telemetry commit atomically. Event identity: the authenticated
        # actor (user_id) and the actor session (session_id); the target
        # account id/username go in sanitized metadata. No password, password
        # hash, session secret or CSRF token may ever enter event metadata.
        db.flush()
        session_service.record_security_event(
            db,
            session_service.EVENT_ACCOUNT_PROVISIONED,
            user_id=current_user.id,
            session_id=_csrf.id,
            success=True,
            metadata={
                "target_user_id": user.id,
                "target_username": user.username,
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered.",
        )
    db.refresh(user)
    return _user_response(user)


@router.post(
    "/users/{user_id}/approve",
    response_model=UserResponse,
    summary="Approve a pending account (centralized authorization: ACCOUNT_APPROVE)",
)
def approve_user(
    user_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission(perm.ACCOUNT_APPROVE)),
    _csrf: AuthSession = Depends(require_csrf),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_approved:
        return _user_response(user)
    user.is_approved = True
    session_service.record_security_event(
        db,
        session_service.EVENT_ACCOUNT_APPROVED,
        user_id=current_user.id,
        session_id=_csrf.id,
        success=True,
        metadata={"target_username": user.username},
    )
    db.commit()
    db.refresh(user)
    return _user_response(user)


@router.post(
    "/users/{user_id}/reject",
    summary="Reject and remove a pending account (centralized authorization: ACCOUNT_REJECT)",
)
def reject_user(
    user_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission(perm.ACCOUNT_REJECT)),
    _csrf: AuthSession = Depends(require_csrf),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_approved:
        # An approved account has moved past the REJECT lifecycle stage
        # (PROVISION -> ACTIVE + UNAPPROVED -> REJECT). Rejecting it would
        # circumvent the lifecycle boundary and delete a treated-as-complete
        # account, so preserve it and fail with a state conflict. No
        # ACCOUNT_REJECTED telemetry is emitted, since the account is not
        # actually being rejected.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot reject an already approved account.",
        )
    target_username = user.username
    db.delete(user)
    session_service.record_security_event(
        db,
        session_service.EVENT_ACCOUNT_REJECTED,
        user_id=current_user.id,
        session_id=_csrf.id,
        success=True,
        metadata={"target_username": target_username},
    )
    db.commit()
    return {"status": "User rejected and removed"}
