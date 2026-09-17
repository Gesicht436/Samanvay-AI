from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.app.models.tables import InventoryItem, InventoryLock, AuditLog
from backend.app.schemas.inventory import InventoryStatus, InventoryItemResponse
from backend.app.core.exceptions import ResourceNotFoundError, IdempotencyConflictError
from backend.app.services.audit_service import create_audit_entry

def list_inventory(db: Session, filters: Dict[str, Any], pagination: Dict[str, int], requesting_cpse: str) -> List[Dict[str, Any]]:
    query = db.query(InventoryItem)
    if "cpse" in filters and filters["cpse"]:
        query = query.filter(InventoryItem.cpse == filters["cpse"])
    if "depot" in filters and filters["depot"]:
        query = query.filter(InventoryItem.depot_id == filters["depot"])
    if "status" in filters and filters["status"]:
        query = query.filter(InventoryItem.status == filters["status"])
    if "item_type" in filters and filters["item_type"]:
        query = query.filter(InventoryItem.item_type == filters["item_type"])
        
    items = query.offset(pagination.get("skip", 0)).limit(pagination.get("limit", 100)).all()
    
    result = []
    for item in items:
        item_dict = item.__dict__.copy()
        if item.cpse != requesting_cpse:
            item_dict.pop("unit_cost_inr", None)
            item_dict.pop("total_value_inr", None)
            item_dict.pop("po_no", None)
            item_dict.pop("vendor_info", None)
        result.append(item_dict)
    return result

def get_item(db: Session, sku_code: str, requesting_cpse: str) -> Dict[str, Any]:
    item = db.query(InventoryItem).filter(InventoryItem.sku_code == sku_code).first()
    if not item:
        raise ResourceNotFoundError(f"Item with SKU {sku_code} not found")
        
    item_dict = item.__dict__.copy()
    if item.cpse != requesting_cpse:
        item_dict.pop("unit_cost_inr", None)
        item_dict.pop("total_value_inr", None)
        item_dict.pop("po_no", None)
        item_dict.pop("vendor_info", None)
    return item_dict

def create_item(db: Session, request: Dict[str, Any]) -> InventoryItem:
    item = InventoryItem(**request)
    db.add(item)
    try:
        db.commit()
        db.refresh(item)
        # Log to audit
        create_audit_entry(db, {"action": "CREATE_INVENTORY", "actor": "SYSTEM", "payload": {"sku_code": item.sku_code}})
        return item
    except IntegrityError:
        db.rollback()
        raise Exception("Failed to create inventory item")

def transition_status(db: Session, sku_code: str, new_status: str, reason: str, officer: str) -> InventoryItem:
    item = db.query(InventoryItem).filter(InventoryItem.sku_code == sku_code).first()
    if not item:
        raise ResourceNotFoundError(f"Item with SKU {sku_code} not found")
        
    old_status = item.status
    item.status = new_status
    db.commit()
    db.refresh(item)
    
    create_audit_entry(db, {
        "action": "TRANSITION_STATUS",
        "actor": officer,
        "payload": {"sku_code": sku_code, "old_status": old_status, "new_status": new_status, "reason": reason}
    })
    
    return item

def get_surplus_radar(db: Session, requesting_cpse: str) -> List[Dict[str, Any]]:
    items = db.query(InventoryItem).filter(InventoryItem.status == "IDLE_SURPLUS").all()
    result = []
    for item in items:
        if item.cpse == requesting_cpse:
            continue # Cross-CPSE only
        item_dict = item.__dict__.copy()
        item_dict.pop("unit_cost_inr", None)
        item_dict.pop("total_value_inr", None)
        item_dict.pop("po_no", None)
        item_dict.pop("vendor_info", None)
        result.append(item_dict)
    return result

def get_hitl_queue(db: Session) -> List[InventoryItem]:
    # Placeholder for items requiring HITL review
    items = db.query(InventoryItem).filter(InventoryItem.is_incomplete == True).all()
    return items
