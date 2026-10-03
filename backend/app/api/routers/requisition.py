from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any
from backend.app.api.dependencies import (
    get_db_session,
    validate_idempotency_key,
    require_any_permission,
    require_csrf,
    require_permission,
)
from backend.app.core import permissions as perm
from backend.app.models.tables import AuthSession, Requisition, User
from backend.app.services.requisition_service import (
    create_requisition,
    approve_requisition,
    reject_requisition,
    generate_gate_pass,
    list_requisitions_for_user,
    get_requisition_for_user,
    dispatch_requisition,
    deliver_requisition,
)
from backend.app.core.exceptions import ResourceNotFoundError

router = APIRouter(prefix="/requisition", tags=["Requisition"])


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_req(
    payload: Dict[str, Any],
    # Authentication and authorization are declared before the idempotency
    # dependency so a replayed key can never be answered before the caller is
    # authenticated, authorized and CSRF-verified.
    current_user: User = Depends(require_permission(perm.REQUISITION_CREATE)),
    _csrf: AuthSession = Depends(require_csrf),
    idempotency_key: str = Depends(validate_idempotency_key),
    db: Session = Depends(get_db_session),
):
    if isinstance(idempotency_key, dict) and idempotency_key.get("status") == "CACHED":
        return idempotency_key["data"]
    try:
        # Bind authenticated requester identity. Role, CPSE and depot are taken
        # from the session only; client-supplied identity never establishes
        # authorization (AUTH-007 Sections 15 and 18).
        payload["requested_by"] = current_user.username
        if current_user.cpse:
            payload["target_cpse"] = current_user.cpse
        if current_user.depot_id:
            payload["target_depot"] = current_user.depot_id
        # The supplying side is owned by the locked inventory record, so any
        # client-selected supplier tenant/depot is discarded here and the
        # service falls back to item.cpse / item.depot_id.
        for client_supplied_field in ("source_cpse", "source_depot", "supplying_cpse", "supplying_depot"):
            payload.pop(client_supplied_field, None)

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
    current_user: User = Depends(require_permission(perm.REQUISITION_READ)),
    db: Session = Depends(get_db_session),
):
    # Tenant boundary: the collection is filtered at query level from the
    # authenticated session identity. No client-supplied CPSE/depot filter and
    # no SUPER_ADMIN cross-tenant visibility.
    return list_requisitions_for_user(db, current_user)


@router.get("/{req_id}")
def get_req(
    req_id: str,
    current_user: User = Depends(require_permission(perm.REQUISITION_READ)),
    db: Session = Depends(get_db_session),
):
    try:
        return get_requisition_for_user(db, req_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{req_id}/approve")
def approve_req(
    req_id: str,
    payload: Dict[str, Any],
    current_user: User = Depends(
        require_any_permission(
            perm.REQUISITION_APPROVE_STANDARD,
            perm.REQUISITION_APPROVE_TECHNICAL,
        )
    ),
    _csrf: AuthSession = Depends(require_csrf),
    db: Session = Depends(get_db_session),
):
    try:
        req_record = db.query(Requisition).filter(Requisition.requisition_id == req_id).first()
        if not req_record:
            raise ResourceNotFoundError(f"Requisition {req_id} not found")
        # Segregation of duties: Requester cannot approve their own requisition.
        # Applies to every role, with no SUPER_ADMIN exemption.
        if req_record.requested_by == current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Segregation of duties violation: Requester cannot approve their own requisition.",
            )
        # Only the supplying CPSE may authorize release of its surplus material.
        if current_user.cpse and req_record.source_cpse and current_user.cpse != req_record.source_cpse:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Only materials managers from supplying CPSE ({req_record.source_cpse}) can approve.",
            )

        req = approve_requisition(db, req_id, current_user.username)
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
    current_user: User = Depends(require_permission(perm.REQUISITION_REJECT)),
    _csrf: AuthSession = Depends(require_csrf),
    db: Session = Depends(get_db_session),
):
    try:
        req_record = db.query(Requisition).filter(Requisition.requisition_id == req_id).first()
        if not req_record:
            raise ResourceNotFoundError(f"Requisition {req_id} not found")
        # Can reject if requester is cancelling, or the supplying CPSE is declining.
        # Applies to every role, with no SUPER_ADMIN exemption.
        if req_record.requested_by != current_user.username and (current_user.cpse and req_record.source_cpse and current_user.cpse != req_record.source_cpse):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Not authorized to reject requisition {req_id}.",
            )

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
    current_user: User = Depends(require_permission(perm.REQUISITION_GATEPASS)),
    _csrf: AuthSession = Depends(require_csrf),
    idempotency_key: str = Depends(validate_idempotency_key),
    db: Session = Depends(get_db_session),
):
    if isinstance(idempotency_key, dict) and idempotency_key.get("status") == "CACHED":
        return idempotency_key["data"]
    try:
        req_record = db.query(Requisition).filter(Requisition.requisition_id == req_id).first()
        if not req_record:
            raise ResourceNotFoundError(f"Requisition {req_id} not found")
        # Only the supplying CPSE may issue a material transfer gate pass.
        # Applies to every role, with no SUPER_ADMIN exemption.
        if current_user.cpse and req_record.source_cpse and current_user.cpse != req_record.source_cpse:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Gate pass can only be issued by supplying CPSE ({req_record.source_cpse}) personnel.",
            )
        payload["issuing_officer"] = f"{current_user.username} ({current_user.role})"

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
    current_user: User = Depends(require_permission(perm.REQUISITION_DISPATCH)),
    _csrf: AuthSession = Depends(require_csrf),
    db: Session = Depends(get_db_session),
):
    try:
        req_record = db.query(Requisition).filter(Requisition.requisition_id == req_id).first()
        if not req_record:
            raise ResourceNotFoundError(f"Requisition {req_id} not found")
        # Only the supplying CPSE may dispatch released material out of its depot.
        # Applies to every role, with no SUPER_ADMIN exemption.
        if current_user.cpse and req_record.source_cpse and current_user.cpse != req_record.source_cpse:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Dispatch is restricted to the supplying CPSE ({req_record.source_cpse}).",
            )
        # Workflow state: a CISF gate pass must have been issued before the
        # consignment leaves the source depot.
        if req_record.status != "GATE_PASS_ISSUED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Requisition {req_id} cannot be dispatched from status '{req_record.status}': status 'GATE_PASS_ISSUED' is required.",
            )

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
    current_user: User = Depends(require_permission(perm.REQUISITION_RECEIVE)),
    _csrf: AuthSession = Depends(require_csrf),
    db: Session = Depends(get_db_session),
):
    try:
        req_record = db.query(Requisition).filter(Requisition.requisition_id == req_id).first()
        if not req_record:
            raise ResourceNotFoundError(f"Requisition {req_id} not found")
        # Receipt is confirmed by the receiving CPSE that raised the requisition.
        # Applies to every role, with no SUPER_ADMIN exemption.
        if current_user.cpse and req_record.target_cpse and current_user.cpse != req_record.target_cpse:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Delivery can only be confirmed by the receiving CPSE ({req_record.target_cpse}).",
            )
        # Workflow state: receipt can only be confirmed for an in-transit
        # consignment.
        if req_record.status != "DISPATCHED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Requisition {req_id} cannot be delivered from status '{req_record.status}': status 'DISPATCHED' is required.",
            )

        req = deliver_requisition(db, req_id)
        return {
            "status": "SUCCESS",
            "requisition_id": req.requisition_id,
            "new_status": req.status,
            "delivery_timestamp": req.delivery_timestamp.isoformat() if req.delivery_timestamp else None,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
