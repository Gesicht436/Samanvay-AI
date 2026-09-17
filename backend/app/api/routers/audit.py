from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from backend.app.api.dependencies import get_db_session, PaginationParams
from backend.app.services.audit_service import verify_chain, export_csv, create_audit_entry

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("/")
def list_audit_entries(pagination: PaginationParams = Depends(), db: Session = Depends(get_db_session)):
    # Simple list (placeholder)
    return {"message": "List audit entries", "skip": pagination.skip, "limit": pagination.limit}

@router.get("/{log_id}")
def get_audit_entry(log_id: int, db: Session = Depends(get_db_session)):
    return {"message": f"Get audit entry {log_id}"}

@router.post("/verify")
def verify_audit_chain(db: Session = Depends(get_db_session)):
    result = verify_chain(db)
    return {"is_valid": result.is_valid, "invalid_entries": result.invalid_entries}

@router.get("/export")
def export_audit_csv(db: Session = Depends(get_db_session)):
    csv_data = export_csv(db, {})
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=audit_export.csv"})

@router.post("/feedback")
def submit_feedback(payload: Dict[str, Any], db: Session = Depends(get_db_session)):
    create_audit_entry(db, {
        "action": "HITL_FEEDBACK",
        "actor": payload.get("actor", "SYSTEM"),
        "payload": payload
    })
    return {"status": "success"}
