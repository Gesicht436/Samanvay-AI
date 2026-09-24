from fastapi import Request, Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from backend.app.models.base import get_db
from backend.app.models.tables import IdempotencyKey, User
from backend.app.core.security import decode_access_token

security_bearer = HTTPBearer(auto_error=False)


async def get_db_session() -> Session:
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db_session),
) -> User:
    """
    Extracts and validates the Bearer JWT token from 'Authorization: Bearer <token>'.
    Returns the authenticated User record from the database.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide 'Authorization: Bearer <token>' header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or malformed access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload["sub"]
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User account '{username}' no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Contact system administrator.",
        )

    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db_session),
) -> Optional[User]:
    """Returns the authenticated user if Bearer token is present, else None."""
    if not credentials or not credentials.credentials:
        return None

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None

    return db.query(User).filter(User.username == payload["sub"]).first()


def require_roles(allowed_roles: List[str]):
    """Enforces Role-Based Access Control on endpoint execution."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and current_user.role != "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: endpoint requires one of {allowed_roles}. Your role is '{current_user.role}'.",
            )
        return current_user
    return role_checker


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
    request: Request,
    x_cpse: Optional[str] = Header(default=None, alias="X-CPSE-ID"),
    current_user: Optional[User] = Depends(get_optional_user),
) -> str:
    """
    Dependency to determine requesting CPSE for privacy filtering.
    Prioritizes authenticated user CPSE, then X-CPSE-ID header, defaulting to OIL.
    """
    if current_user and current_user.cpse:
        return current_user.cpse
    if x_cpse:
        return x_cpse
    return "OIL"


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
