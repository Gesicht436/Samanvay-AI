import uuid
import hashlib
import io
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import qrcode
import qrcode.image.svg
from sqlalchemy.orm import Session

from backend.app.models.tables import Requisition, InventoryItem, InventoryLock, DigitalGatePass
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.services.audit_service import create_audit_entry
from backend.app.core.security import compute_gate_pass_seal, compute_sha256
from graph.logistics import road_distance, estimate_transit_hours, compute_co2_saved, DEPOT_COORDINATES


def list_requisitions(db: Session, cpse: Optional[str] = None) -> List[Dict[str, Any]]:
    query = db.query(Requisition)
    if cpse and cpse != "ALL":
        query = query.filter((Requisition.source_cpse == cpse) | (Requisition.target_cpse == cpse))
    reqs = query.order_by(Requisition.created_at.desc()).all()
    return [
        {c.name: getattr(r, c.name) for c in r.__table__.columns}
        for r in reqs
    ]


def get_requisition(db: Session, req_id: str) -> Dict[str, Any]:
    req = db.query(Requisition).filter(Requisition.requisition_id == req_id).first()
    if not req:
        raise ResourceNotFoundError(f"Requisition {req_id} not found")
    data = {c.name: getattr(req, c.name) for c in req.__table__.columns}
    # Include associated gate pass if available
    gp = db.query(DigitalGatePass).filter(DigitalGatePass.requisition_id == req_id).first()
    if gp:
        data["gate_pass"] = {c.name: getattr(gp, c.name) for c in gp.__table__.columns}
    return data


def create_requisition(db: Session, request: Dict[str, Any], idempotency_key: str) -> Requisition:
    sku_code = request.get("sku_code")
    quantity = int(request.get("required_qty") or request.get("quantity", 1))

    # Atomic lock on inventory item using SELECT ... FOR UPDATE
    item = db.query(InventoryItem).filter(InventoryItem.sku_code == sku_code).with_for_update().first()
    if not item:
        raise ResourceNotFoundError(f"Inventory Item {sku_code} not found")

    if item.quantity < quantity:
        raise ValueError(f"Insufficient stock: requested {quantity} EA, available {item.quantity} EA")

    req_id = request.get("requisition_id") or f"REQ-{uuid.uuid4().hex[:6].upper()}"
    unit_cost = float(request.get("unit_cost_inr") or item.unit_cost_inr or 0.0)
    total_val = unit_cost * quantity

    audit_hash = compute_sha256(f"{req_id}|{sku_code}|{quantity}|{datetime.now(timezone.utc).isoformat()}")

    req = Requisition(
        requisition_id=req_id,
        source_cpse=request.get("source_cpse", item.cpse),
        source_depot=request.get("source_depot", item.depot_id),
        source_unit=request.get("source_unit", "Main Depot Stores"),
        target_cpse=request.get("target_cpse", "ONGC"),
        target_depot=request.get("target_depot", "Uran Gas Plant"),
        sku_code=sku_code,
        item_description=request.get("item_description", item.description),
        required_qty=quantity,
        unit_cost_inr=unit_cost,
        total_value_inr=total_val,
        justification=request.get("justification", "Emergency mutual aid requisition"),
        urgency_level=request.get("urgency_level", "EMERGENCY"),
        status="PENDING_APPROVAL",
        requested_by=request.get("requested_by", "MATERIALS_ENGINEER"),
        audit_hash=audit_hash,
    )
    db.add(req)
    db.flush()

    # Reserve locked quantity
    lock = InventoryLock(
        sku_code=sku_code,
        requisition_id=req.requisition_id,
        locked_qty=quantity,
        locked_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_active=True,
    )
    db.add(lock)

    # Debit available inventory
    item.quantity -= quantity

    create_audit_entry(db, {
        "action_category": "REQUISITION",
        "action": "CREATE_REQUISITION",
        "actor": request.get("requested_by", "MATERIALS_ENGINEER"),
        "cpse": req.target_cpse,
        "depot": req.target_depot,
        "reference_id": req.requisition_id,
        "payload": {
            "requisition_id": req.requisition_id,
            "sku_code": sku_code,
            "quantity": quantity,
        },
    })

    db.commit()
    db.refresh(req)
    return req


def approve_requisition(db: Session, req_id: str, approved_by: str) -> Requisition:
    req = db.query(Requisition).filter(Requisition.requisition_id == req_id).first()
    if not req:
        raise ResourceNotFoundError(f"Requisition {req_id} not found")

    req.status = "APPROVED"
    req.approved_by = approved_by
    req.approved_at = datetime.now(timezone.utc)

    create_audit_entry(db, {
        "action_category": "REQUISITION",
        "action": "APPROVE_REQUISITION",
        "actor": approved_by,
        "cpse": req.source_cpse,
        "depot": req.source_depot,
        "reference_id": req.requisition_id,
        "payload": {"requisition_id": req.requisition_id, "approved_by": approved_by},
    })

    db.commit()
    db.refresh(req)
    return req


def reject_requisition(db: Session, req_id: str, reason: str) -> Requisition:
    req = db.query(Requisition).filter(Requisition.requisition_id == req_id).first()
    if not req:
        raise ResourceNotFoundError(f"Requisition {req_id} not found")

    req.status = "REJECTED"
    req.rejection_reason = reason

    # Release lock and restore quantity
    lock = db.query(InventoryLock).filter(
        InventoryLock.requisition_id == req.requisition_id,
        InventoryLock.is_active == True,
    ).first()
    if lock:
        item = db.query(InventoryItem).filter(InventoryItem.sku_code == lock.sku_code).first()
        if item:
            item.quantity += lock.locked_qty
        lock.is_active = False

    create_audit_entry(db, {
        "action_category": "REQUISITION",
        "action": "REJECT_REQUISITION",
        "actor": "SYSTEM",
        "cpse": req.source_cpse,
        "depot": req.source_depot,
        "reference_id": req.requisition_id,
        "payload": {"requisition_id": req.requisition_id, "reason": reason},
    })

    db.commit()
    db.refresh(req)
    return req


def generate_gate_pass(db: Session, req_id: str, gate_pass_request: Dict[str, Any]) -> DigitalGatePass:
    req = db.query(Requisition).filter(Requisition.requisition_id == req_id).first()
    if not req or req.status != "APPROVED":
        raise ValueError(f"Requisition {req_id} must be APPROVED before generating gate pass")

    depot_code = gate_pass_request.get("depot_code", "PNP")
    serial = f"{uuid.uuid4().hex[:6].upper()}"
    gp_number = f"MoPNG/CISF/GP-NR/2026/{serial}"

    issuing_officer = gate_pass_request.get("issuing_officer", "INSPECTOR_CISF_PANIPAT")
    vehicle_no = gate_pass_request.get("vehicle_no", "HR-06-EA-8841")
    driver_id = gate_pass_request.get("driver_id", "DL-04201988102")
    timestamp_str = datetime.now(timezone.utc).isoformat()

    # Calculate logistics metrics
    src_coord = DEPOT_COORDINATES.get("Panipat", (29.3909, 76.9635))
    tgt_coord = DEPOT_COORDINATES.get("Visakh", (17.6868, 83.2185))
    distance_km = road_distance(src_coord[0], src_coord[1], tgt_coord[0], tgt_coord[1])
    transit_hrs = int(estimate_transit_hours(distance_km))
    co2_saved = compute_co2_saved(distance_km)

    seal = compute_gate_pass_seal(
        gate_pass_no=gp_number,
        vehicle_no=vehicle_no,
        driver_id=driver_id,
        sku_code=req.sku_code,
        quantity=req.required_qty,
        issuing_officer=issuing_officer,
        timestamp=timestamp_str,
    )

    factory = qrcode.image.svg.SvgImage
    qr_payload = f"Samanvay-AI|{gp_number}|{req.requisition_id}|{req.sku_code}|{seal[:16]}"
    img = qrcode.make(qr_payload, image_factory=factory)
    svg_io = io.BytesIO()
    img.save(svg_io)
    svg_content = svg_io.getvalue().decode("utf-8")

    gp = DigitalGatePass(
        gate_pass_no=gp_number,
        requisition_id=req.requisition_id,
        issuing_cpse=req.source_cpse,
        issuing_depot=req.source_depot,
        receiving_cpse=req.target_cpse,
        receiving_depot=req.target_depot,
        transporter_name=gate_pass_request.get("transporter_name", "CONCOR Heavy Logistics"),
        vehicle_no=vehicle_no,
        driver_name=gate_pass_request.get("driver_name", "B. Singh"),
        driver_id_no=driver_id,
        gst_eway_bill_no=gate_pass_request.get("gst_eway_bill_no", f"EWB-2026-{serial}"),
        cisf_verification_seal=f"CISF-POST-04-{depot_code}",
        sha256_hash=seal,
        transit_distance_km=distance_km,
        co2_saved_kg=co2_saved,
        estimated_transit_hours=transit_hrs,
        qr_code_svg=svg_content,
    )
    db.add(gp)
    req.status = "GATE_PASS_ISSUED"

    create_audit_entry(db, {
        "action_category": "GATE_PASS",
        "action": "GENERATE_GATE_PASS",
        "actor": issuing_officer,
        "cpse": req.source_cpse,
        "depot": req.source_depot,
        "reference_id": gp_number,
        "payload": {
            "requisition_id": req.requisition_id,
            "gate_pass_no": gp_number,
            "sha256_seal": seal,
        },
    })

    db.commit()
    db.refresh(gp)
    return gp


def dispatch_requisition(db: Session, req_id: str) -> Requisition:
    req = db.query(Requisition).filter(Requisition.requisition_id == req_id).first()
    if not req:
        raise ResourceNotFoundError(f"Requisition {req_id} not found")

    req.status = "DISPATCHED"
    req.dispatch_timestamp = datetime.now(timezone.utc)

    create_audit_entry(db, {
        "action_category": "DISPATCH",
        "action": "DISPATCH_REQUISITION",
        "actor": "CISF_SECURITY_OUT_GATE",
        "cpse": req.source_cpse,
        "depot": req.source_depot,
        "reference_id": req.requisition_id,
        "payload": {"requisition_id": req.requisition_id, "status": "DISPATCHED"},
    })

    db.commit()
    db.refresh(req)
    return req


def deliver_requisition(db: Session, req_id: str) -> Requisition:
    req = db.query(Requisition).filter(Requisition.requisition_id == req_id).first()
    if not req:
        raise ResourceNotFoundError(f"Requisition {req_id} not found")

    req.status = "DELIVERED"
    req.delivery_timestamp = datetime.now(timezone.utc)

    # Release the inventory lock permanently
    lock = db.query(InventoryLock).filter(
        InventoryLock.requisition_id == req.requisition_id,
        InventoryLock.is_active == True,
    ).first()
    if lock:
        lock.is_active = False

    create_audit_entry(db, {
        "action_category": "DISPATCH",
        "action": "DELIVER_REQUISITION",
        "actor": "CISF_SECURITY_IN_GATE",
        "cpse": req.target_cpse,
        "depot": req.target_depot,
        "reference_id": req.requisition_id,
        "payload": {"requisition_id": req.requisition_id, "status": "DELIVERED"},
    })

    db.commit()
    db.refresh(req)
    return req
