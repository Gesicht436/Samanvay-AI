from fastapi import Request, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone, timedelta
from backend.app.models.base import get_db
from backend.app.models.tables import IdempotencyKey


async def get_db_session() -> Session:
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


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


def verify_cpse_access(request: Request, x_cpse: str = Header(default="IOCL", alias="X-CPSE-ID")) -> str:
    """Dependency to determine requesting CPSE for privacy filtering."""
    if not x_cpse:
        return "IOCL"
    return x_cpse


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
