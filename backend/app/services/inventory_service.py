from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.app.models.tables import InventoryItem, InventoryLock, SovereignAuditLedger
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.services.audit_service import create_audit_entry


def list_inventory(
    db: Session,
    filters: Dict[str, Any],
    pagination: Dict[str, int],
    requesting_cpse: str,
) -> Dict[str, Any]:
    # Tenant boundary is applied at query level and comes ONLY from the
    # authenticated session. A client-supplied ``cpse`` filter is deliberately
    # NOT honoured as a tenant selector: it can neither broaden nor switch the
    # caller's CPSE. ``depot``/``status``/``item_type`` may only narrow within it.
    query = db.query(InventoryItem).filter(InventoryItem.cpse == requesting_cpse)
    if "depot" in filters and filters["depot"] and filters["depot"] != "ALL":
        query = query.filter(InventoryItem.depot_id == filters["depot"])
    if "status" in filters and filters["status"] and filters["status"] != "ALL":
        query = query.filter(InventoryItem.status == filters["status"])
    if "item_type" in filters and filters["item_type"] and filters["item_type"] != "ALL":
        query = query.filter(InventoryItem.item_type == filters["item_type"])

    total = query.count()
    items = query.offset(pagination.get("skip", 0)).limit(pagination.get("limit", 100)).all()

    result = []
    for item in items:
        item_dict = {
            c.name: getattr(item, c.name)
            for c in item.__table__.columns
        }
        # Strict Attribute-Level Privacy: strip commercial prices for cross-CPSE callers
        if item.cpse != requesting_cpse:
            item_dict.pop("unit_cost_inr", None)
            item_dict.pop("total_value_inr", None)
            item_dict.pop("po_no", None)

        result.append(item_dict)

    return {
        "total": total,
        "skip": pagination.get("skip", 0),
        "limit": pagination.get("limit", 100),
        "items": result,
    }


def get_item(db: Session, sku_code: str, requesting_cpse: str) -> Dict[str, Any]:
    # Tenant isolation is part of the lookup predicate: a SKU owned by another
    # CPSE is indistinguishable from a nonexistent SKU (ResourceNotFoundError).
    item = db.query(InventoryItem).filter(
        InventoryItem.sku_code == sku_code,
        InventoryItem.cpse == requesting_cpse,
    ).first()
    if not item:
        raise ResourceNotFoundError(f"Item with SKU {sku_code} not found")

    item_dict = {
        c.name: getattr(item, c.name)
        for c in item.__table__.columns
    }
    # Enforce Attribute-Level Privacy
    if item.cpse != requesting_cpse:
        item_dict.pop("unit_cost_inr", None)
        item_dict.pop("total_value_inr", None)
        item_dict.pop("po_no", None)

    return item_dict


def create_item(
    db: Session,
    request: Dict[str, Any],
    requesting_cpse: str,
    actor: str,
) -> InventoryItem:
    # Tenant boundary (AUTH-007): the authenticated session CPSE is authoritative.
    # A client-supplied ``cpse`` can neither select nor broaden the stored tenant,
    # so it is overwritten unconditionally rather than rejected.
    effective_cpse = requesting_cpse.strip().upper()
    item = InventoryItem(**{**request, "cpse": effective_cpse})
    db.add(item)
    try:
        db.commit()
        db.refresh(item)
        create_audit_entry(db, {
            "action_category": "STATUS_CHANGE",
            "action": "CREATE_INVENTORY",
            "actor": actor,
            "cpse": item.cpse,
            "depot": item.depot_id,
            "reference_id": item.sku_code,
            "payload": {"sku_code": item.sku_code, "quantity": item.quantity},
        })
        return item
    except IntegrityError:
        db.rollback()
        raise Exception("Failed to create inventory item: SKU conflict or constraint violation")


def transition_status(
    db: Session,
    sku_code: str,
    new_status: str,
    reason: str,
    officer: str,
    requesting_cpse: str,
) -> InventoryItem:
    # Tenant isolation is part of the lookup predicate: a SKU owned by another
    # CPSE is indistinguishable from a nonexistent SKU (ResourceNotFoundError).
    item = db.query(InventoryItem).filter(
        InventoryItem.sku_code == sku_code,
        InventoryItem.cpse == requesting_cpse,
    ).first()
    if not item:
        raise ResourceNotFoundError(f"Item with SKU {sku_code} not found")

    old_status = item.status
    item.status = new_status
    if new_status == "IDLE_SURPLUS":
        item.is_broadcasted_surplus = True

    db.commit()
    db.refresh(item)

    create_audit_entry(db, {
        "action_category": "STATUS_CHANGE",
        "action": "TRANSITION_STATUS",
        "actor": officer,
        "cpse": item.cpse,
        "depot": item.depot_id,
        "reference_id": sku_code,
        "payload": {
            "sku_code": sku_code,
            "old_status": old_status,
            "new_status": new_status,
            "reason": reason,
        },
    })

    return item


def get_surplus_radar(db: Session, requesting_cpse: str) -> List[Dict[str, Any]]:
    """
    Returns available idle surplus items across sister CPSEs with commercial prices protected.
    """
    items = (
        db.query(InventoryItem)
        .filter(
            (InventoryItem.status == "IDLE_SURPLUS") | (InventoryItem.is_broadcasted_surplus == True)
        )
        .all()
    )
    result = []
    for item in items:
        if item.cpse == requesting_cpse:
            continue  # Cross-CPSE only

        item_dict = {
            c.name: getattr(item, c.name)
            for c in item.__table__.columns
        }
        # Strip commercial prices
        item_dict.pop("unit_cost_inr", None)
        item_dict.pop("total_value_inr", None)
        item_dict.pop("po_no", None)

        result.append(item_dict)

    return result


def get_hitl_queue(db: Session, requesting_cpse: str) -> List[Dict[str, Any]]:
    """
    Retrieves items requiring Human-In-The-Loop review (unverified MTCs or conditional
    tolerance matches) for the authenticated session's CPSE only.
    """
    items = (
        db.query(InventoryItem)
        .filter(
            InventoryItem.cpse == requesting_cpse,
            (InventoryItem.status == "HITL_REVIEW") | (InventoryItem.days_idle >= 90),
        )
        .all()
    )
    return [
        {c.name: getattr(item, c.name) for c in item.__table__.columns}
        for item in items
    ]


def get_inventory_stats(db: Session, requesting_cpse: str) -> Dict[str, Any]:
    """
    Computes aggregate metrics across the sovereign inventory and requisition ledgers.
    """
    from sqlalchemy import func, or_
    from backend.app.models.tables import Requisition

    # Every aggregate below is scoped at query level to the authenticated
    # session's CPSE; no other CPSE's counts, values or categories are exposed.
    total_items = db.query(InventoryItem).filter(
        InventoryItem.cpse == requesting_cpse
    ).count()
    total_surplus = db.query(InventoryItem).filter(
        InventoryItem.cpse == requesting_cpse,
        (InventoryItem.status == "IDLE_SURPLUS") | (InventoryItem.is_broadcasted_surplus == True),
    ).count()
    total_hitl = db.query(InventoryItem).filter(
        InventoryItem.cpse == requesting_cpse,
        (InventoryItem.status == "HITL_REVIEW") | (InventoryItem.days_idle >= 90),
    ).count()
    # Requisition exposes both sides of the transfer (``source_cpse`` /
    # ``target_cpse``); count only those the caller's CPSE participates in, using
    # the existing columns. No new tenant field is introduced.
    total_requisitions = db.query(Requisition).filter(
        or_(
            Requisition.source_cpse == requesting_cpse,
            Requisition.target_cpse == requesting_cpse,
        )
    ).count()

    capital_res = db.query(func.sum(InventoryItem.total_value_inr)).filter(
        InventoryItem.cpse == requesting_cpse,
        (InventoryItem.status == "IDLE_SURPLUS") | (InventoryItem.is_broadcasted_surplus == True),
    ).scalar()
    capital_unlocked_cr = round(float(capital_res or 0.0) / 1e7, 2)

    cpse_rows = db.query(
        InventoryItem.cpse,
        func.count(InventoryItem.id).label("count"),
        func.sum(InventoryItem.total_value_inr).label("total_val")
    ).filter(
        InventoryItem.cpse == requesting_cpse
    ).group_by(InventoryItem.cpse).all()

    cpse_breakdown = [
        {
            "cpse": row.cpse,
            "count": row.count,
            "total_value_cr": round(float(row.total_val or 0.0) / 1e7, 2),
        }
        for row in cpse_rows
    ]

    cat_rows = db.query(
        InventoryItem.item_type,
        func.count(InventoryItem.id).label("count")
    ).filter(
        InventoryItem.cpse == requesting_cpse
    ).group_by(InventoryItem.item_type).all()

    category_breakdown = [
        {"category": row.item_type, "count": row.count}
        for row in cat_rows
    ]

    return {
        "total_items": total_items,
        "total_surplus": total_surplus,
        "total_hitl": total_hitl,
        "total_requisitions": total_requisitions,
        "capital_unlocked_cr": capital_unlocked_cr,
        "cpse_breakdown": cpse_breakdown,
        "category_breakdown": category_breakdown,
    }

