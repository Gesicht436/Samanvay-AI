from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from backend.app.api.dependencies import get_db_session, PaginationParams
from backend.app.services.audit_service import (
    verify_chain,
    export_csv,
    create_audit_entry,
    list_audit_entries,
    get_audit_entry_by_id,
)

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/")
def list_entries(
    pagination: PaginationParams = Depends(),
    category: Optional[str] = Query(default="ALL"),
    cpse: Optional[str] = Query(default="ALL"),
    db: Session = Depends(get_db_session),
):
    return list_audit_entries(
        db,
        skip=pagination.skip,
        limit=pagination.limit,
        category=category,
        cpse=cpse,
    )


@router.get("/verify")
@router.post("/verify")
def verify_audit_chain_endpoint(db: Session = Depends(get_db_session)):
    result = verify_chain(db)
    return {
        "is_valid": result.is_valid,
        "total_verified": result.total_verified,
        "invalid_entries": result.invalid_entries,
    }


@router.get("/export")
def export_audit_csv_endpoint(
    category: Optional[str] = Query(default=None),
    cpse: Optional[str] = Query(default=None),
    db: Session = Depends(get_db_session),
):
    filters = {}
    if category and category != "ALL":
        filters["category"] = category
    if cpse and cpse != "ALL":
        filters["cpse"] = cpse

    csv_data = export_csv(db, filters)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=samanvay_sovereign_audit_ledger.csv"},
    )


@router.get("/{log_id}")
def get_entry(log_id: str, db: Session = Depends(get_db_session)):
    entry = get_audit_entry_by_id(db, log_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Audit entry {log_id} not found")
    return {
        "log_id": entry.log_id,
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        "action_category": entry.action_category,
        "action_name": entry.action_name,
        "actor_name": entry.actor_name,
        "actor_role": entry.actor_role,
        "cpse": entry.cpse,
        "depot": entry.depot,
        "reference_id": entry.reference_id,
        "details": entry.details,
        "prev_hash": entry.prev_hash,
        "sha256_hash": entry.sha256_hash,
        "is_verified": entry.is_verified,
    }


@router.post("/feedback")
def submit_feedback(payload: Dict[str, Any], db: Session = Depends(get_db_session)):
    entry = create_audit_entry(db, {
        "action_category": "HITL_TRIAGE",
        "action": "HITL_FEEDBACK",
        "actor": payload.get("actor", "QUALITY_AUDITOR"),
        "cpse": payload.get("cpse", "IOCL"),
        "depot": payload.get("depot", "DEFAULT_DEPOT"),
        "reference_id": payload.get("reference_id", "FEEDBACK-001"),
        "payload": payload,
    })
    return {"status": "SUCCESS", "log_id": entry.log_id, "sha256_hash": entry.sha256_hash}
