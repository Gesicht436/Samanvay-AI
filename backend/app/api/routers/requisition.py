from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any, Optional
from backend.app.api.dependencies import get_db_session, validate_idempotency_key
from backend.app.services.requisition_service import (
    create_requisition,
    approve_requisition,
    reject_requisition,
    generate_gate_pass,
    list_requisitions,
    get_requisition,
    dispatch_requisition,
    deliver_requisition,
)
from backend.app.core.exceptions import ResourceNotFoundError

router = APIRouter(prefix="/requisition", tags=["Requisition"])


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_req(
    payload: Dict[str, Any],
    idempotency_key: str = Depends(validate_idempotency_key),
    db: Session = Depends(get_db_session),
):
    if isinstance(idempotency_key, dict) and idempotency_key.get("status") == "CACHED":
        return idempotency_key["data"]
    try:
        req = create_requisition(db, payload, str(idempotency_key))
        return {
            "status": "SUCCESS",
            "requisition_id": req.requisition_id,
            "sku_code": req.sku_code,
            "quantity": req.required_qty,
            "current_status": req.status,
            "audit_hash": req.audit_hash,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Requisition ID already exists")


@router.get("")
@router.get("/")
def list_reqs(
    cpse: Optional[str] = None,
    db: Session = Depends(get_db_session),
):
    return list_requisitions(db, cpse)


@router.get("/{req_id}")
def get_req(
    req_id: str,
    db: Session = Depends(get_db_session),
):
    try:
        return get_requisition(db, req_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{req_id}/approve")
def approve_req(
    req_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db_session),
):
    try:
        req = approve_requisition(db, req_id, payload.get("approved_by", "SYSTEM_OFFICER"))
        return {
            "status": "SUCCESS",
            "requisition_id": req.requisition_id,
            "new_status": req.status,
            "approved_by": req.approved_by,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{req_id}/reject")
def reject_req(
    req_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db_session),
):
    try:
        req = reject_requisition(db, req_id, payload.get("reason", "Requisition declined by depot"))
        return {
            "status": "SUCCESS",
            "requisition_id": req.requisition_id,
            "new_status": req.status,
            "rejection_reason": req.rejection_reason,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{req_id}/gatepass", status_code=status.HTTP_201_CREATED)
def generate_gp(
    req_id: str,
    payload: Dict[str, Any],
    idempotency_key: str = Depends(validate_idempotency_key),
    db: Session = Depends(get_db_session),
):
    if isinstance(idempotency_key, dict) and idempotency_key.get("status") == "CACHED":
        return idempotency_key["data"]
    try:
        gp = generate_gate_pass(db, req_id, payload)
        return {
            "status": "SUCCESS",
            "gate_pass_no": gp.gate_pass_no,
            "requisition_id": gp.requisition_id,
            "sha256_hash": gp.sha256_hash,
            "qr_code_svg": gp.qr_code_svg,
            "transit_distance_km": float(gp.transit_distance_km),
            "estimated_transit_hours": gp.estimated_transit_hours,
            "co2_saved_kg": float(gp.co2_saved_kg),
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/{req_id}/dispatch")
def dispatch_req(
    req_id: str,
    db: Session = Depends(get_db_session),
):
    try:
        req = dispatch_requisition(db, req_id)
        return {
            "status": "SUCCESS",
            "requisition_id": req.requisition_id,
            "new_status": req.status,
            "dispatch_timestamp": req.dispatch_timestamp.isoformat() if req.dispatch_timestamp else None,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{req_id}/deliver")
def deliver_req(
    req_id: str,
    db: Session = Depends(get_db_session),
):
    try:
        req = deliver_requisition(db, req_id)
        return {
            "status": "SUCCESS",
            "requisition_id": req.requisition_id,
            "new_status": req.status,
            "delivery_timestamp": req.delivery_timestamp.isoformat() if req.delivery_timestamp else None,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
