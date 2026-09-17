from fastapi import Request, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from backend.app.models.base import get_db
from backend.app.models.tables import IdempotencyKey
from datetime import datetime

async def get_db_session() -> Session:
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

def validate_idempotency_key(
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db_session)
):
    key_record = db.query(IdempotencyKey).filter(IdempotencyKey.key == idempotency_key).first()
    if key_record:
        if key_record.status == "IN_FLIGHT":
            raise HTTPException(status_code=409, detail="Request already in flight")
        elif key_record.status == "COMPLETED":
            # Just mimicking a return for cached response
            return {"status": "CACHED", "data": key_record.response_body}
            
    # Record new key
    new_key = IdempotencyKey(
        key=idempotency_key,
        status="IN_FLIGHT",
        created_at=datetime.utcnow()
    )
    db.add(new_key)
    db.commit()
    return idempotency_key

def verify_cpse_access(request: Request, x_cpse: str = Header(..., alias="X-CPSE-ID")) -> str:
    """Dependency to determine requesting CPSE for privacy filtering"""
    if not x_cpse:
        raise HTTPException(status_code=401, detail="X-CPSE-ID header missing")
    return x_cpse

class PaginationParams:
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = skip
        self.limit = limit

class InventoryFilterParams:
    def __init__(self, cpse: Optional[str] = None, depot: Optional[str] = None, status: Optional[str] = None, item_type: Optional[str] = None):
        self.cpse = cpse
        self.depot = depot
        self.status = status
        self.item_type = item_type
