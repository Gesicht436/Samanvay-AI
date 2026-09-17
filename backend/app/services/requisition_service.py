import uuid
import hashlib
import qrcode
import qrcode.image.svg
import io
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any
from backend.app.models.tables import Requisition, InventoryItem, InventoryLock, GatePass
from backend.app.core.exceptions import ResourceNotFoundError, IdempotencyConflictError
from backend.app.services.audit_service import create_audit_entry

def create_requisition(db: Session, request: Dict[str, Any], idempotency_key: str) -> Requisition:
    sku_code = request.get("sku_code")
    quantity = request.get("quantity")
    
    # Atomic lock on inventory item
    item = db.query(InventoryItem).filter(InventoryItem.sku_code == sku_code).with_for_update().first()
    if not item:
        raise ResourceNotFoundError(f"Item {sku_code} not found")
        
    if item.quantity < quantity:
        raise ValueError("Insufficient inventory")
        
    req = Requisition(**request, status="PENDING")
    db.add(req)
    db.flush()
    
    lock = InventoryLock(
        requisition_id=req.id,
        sku_code=sku_code,
        quantity=quantity,
        locked_by=request.get("requesting_cpse")
    )
    db.add(lock)
    
    item.quantity -= quantity
    
    create_audit_entry(db, {
        "action": "CREATE_REQUISITION",
        "actor": request.get("requesting_cpse"),
        "payload": {"requisition_id": req.id, "sku_code": sku_code, "quantity": quantity}
    })
    
    db.commit()
    db.refresh(req)
    return req

def approve_requisition(db: Session, req_id: str, approved_by: str) -> Requisition:
    req = db.query(Requisition).filter(Requisition.id == req_id).first()
    if not req:
        raise ResourceNotFoundError("Requisition not found")
        
    req.status = "APPROVED"
    req.approved_by = approved_by
    
    create_audit_entry(db, {
        "action": "APPROVE_REQUISITION",
        "actor": approved_by,
        "payload": {"requisition_id": req.id}
    })
    
    db.commit()
    db.refresh(req)
    return req

def reject_requisition(db: Session, req_id: str, reason: str) -> Requisition:
    req = db.query(Requisition).filter(Requisition.id == req_id).first()
    if not req:
        raise ResourceNotFoundError("Requisition not found")
        
    req.status = "REJECTED"
    req.rejection_reason = reason
    
    # Release lock and restore quantity
    lock = db.query(InventoryLock).filter(InventoryLock.requisition_id == req.id).first()
    if lock:
        item = db.query(InventoryItem).filter(InventoryItem.sku_code == lock.sku_code).first()
        if item:
            item.quantity += lock.quantity
        db.delete(lock)
        
    create_audit_entry(db, {
        "action": "REJECT_REQUISITION",
        "actor": "SYSTEM",
        "payload": {"requisition_id": req.id, "reason": reason}
    })
    
    db.commit()
    db.refresh(req)
    return req

def generate_gate_pass(db: Session, req_id: str, gate_pass_request: Dict[str, Any]) -> GatePass:
    req = db.query(Requisition).filter(Requisition.id == req_id).first()
    if not req or req.status != "APPROVED":
        raise ValueError("Invalid requisition for gate pass")
        
    depot_code = gate_pass_request.get("depot_code", "UNK")
    serial = f"{uuid.uuid4().hex[:6].upper()}"
    gp_number = f"OGP-2026-{depot_code}-081-{serial}"
    
    seal_content = f"{gp_number}|{req.id}|{req.sku_code}|{req.quantity}"
    seal = hashlib.sha256(seal_content.encode()).hexdigest()
    
    factory = qrcode.image.svg.SvgImage
    img = qrcode.make(f"Samanvay-AI|{gp_number}|{seal}", image_factory=factory)
    svg_io = io.BytesIO()
    img.save(svg_io)
    svg_content = svg_io.getvalue().decode('utf-8')
    
    gp = GatePass(
        requisition_id=req.id,
        gate_pass_number=gp_number,
        seal_hash=seal,
        qr_svg=svg_content,
        transit_distance_km=gate_pass_request.get("distance_km", 0.0),
        lead_time_days=gate_pass_request.get("lead_time_days", 0),
        co2_saved_kg=gate_pass_request.get("co2_saved_kg", 0.0)
    )
    db.add(gp)
    
    create_audit_entry(db, {
        "action": "GENERATE_GATE_PASS",
        "actor": "SYSTEM",
        "payload": {"requisition_id": req.id, "gate_pass_number": gp_number}
    })
    
    db.commit()
    db.refresh(gp)
    return gp
