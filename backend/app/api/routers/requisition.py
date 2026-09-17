from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.app.api.dependencies import get_db_session, validate_idempotency_key
from backend.app.services.requisition_service import create_requisition, approve_requisition, reject_requisition, generate_gate_pass

router = APIRouter(prefix="/requisition", tags=["Requisition"])

@router.post("/")
def create_req(
    payload: Dict[str, Any],
    idempotency_key: str = Depends(validate_idempotency_key),
    db: Session = Depends(get_db_session)
):
    if isinstance(idempotency_key, dict) and idempotency_key.get("status") == "CACHED":
        return idempotency_key["data"]
    return create_requisition(db, payload, idempotency_key)

@router.get("/")
def list_reqs(db: Session = Depends(get_db_session)):
    return {"message": "List requisitions"}

@router.get("/{req_id}")
def get_req(req_id: str, db: Session = Depends(get_db_session)):
    return {"message": f"Get requisition {req_id}"}

@router.put("/{req_id}/approve")
def approve_req(req_id: str, payload: Dict[str, Any], db: Session = Depends(get_db_session)):
    return approve_requisition(db, req_id, payload.get("approved_by", "SYSTEM"))

@router.put("/{req_id}/reject")
def reject_req(req_id: str, payload: Dict[str, Any], db: Session = Depends(get_db_session)):
    return reject_requisition(db, req_id, payload.get("reason", "Unknown"))

@router.post("/{req_id}/gatepass")
def generate_gp(
    req_id: str,
    payload: Dict[str, Any],
    idempotency_key: str = Depends(validate_idempotency_key),
    db: Session = Depends(get_db_session)
):
    if isinstance(idempotency_key, dict) and idempotency_key.get("status") == "CACHED":
        return idempotency_key["data"]
    return generate_gate_pass(db, req_id, payload)

@router.put("/{req_id}/dispatch")
def dispatch_req(req_id: str, db: Session = Depends(get_db_session)):
    return {"message": f"Dispatch requisition {req_id}"}

@router.put("/{req_id}/deliver")
def deliver_req(req_id: str, db: Session = Depends(get_db_session)):
    return {"message": f"Deliver requisition {req_id}"}
