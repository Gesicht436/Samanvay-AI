"""
API V1 Central Inventory & Lifecycle Management Router.
Handles procurement bill confirmation, site engineer review adjustments,
status tagging (TO_BE_CONSUMED, IN_STORAGE, IDLE_SURPLUS, CONSUMED),
and real-time synchronization with the Neo4j Knowledge Graph.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.api.deps import get_db
from backend.app.contracts.inventory import (
    InventoryItemCreate,
    InventoryStatusUpdate,
    InventoryItemResponse,
    InventoryItemStatus,
)
from backend.app.ingestion.storage import (
    create_inventory_item,
    get_inventory_items,
    get_inventory_item_by_id,
    update_inventory_status,
    save_reconciliation_decision,
)
from backend.app.graph.queries import sync_inventory_item_to_graph

router = APIRouter(prefix="/inventory", tags=["Central Inventory & Lifecycle"])


def _to_response(item) -> InventoryItemResponse:
    total_val = round(item.quantity * item.unit_cost_inr, 2)
    return InventoryItemResponse(
        id=item.id,
        sku_code=item.sku_code,
        cpse=item.cpse,
        depot_id=item.depot_id,
        depot_location=item.depot_location,
        po_no=item.po_no,
        heat_no=item.heat_no,
        description=item.description,
        canonical_id=item.canonical_id,
        item_type=item.item_type,
        size_nb_mm=item.size_nb_mm,
        pressure_class=item.pressure_class,
        metallurgy=item.metallurgy,
        facing_end=item.facing_end,
        standard=item.standard,
        quantity=item.quantity,
        unit_cost_inr=item.unit_cost_inr,
        total_value_inr=total_val,
        status=InventoryItemStatus(item.status),
        days_idle=item.days_idle,
        source_document_id=item.source_document_id,
        created_at=item.created_at.isoformat() if item.created_at else None,
        updated_at=item.updated_at.isoformat() if item.updated_at else None,
        is_broadcasted_surplus=(item.status == InventoryItemStatus.IDLE_SURPLUS.value),
    )


@router.post("/commit-bill", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
def commit_procured_bill_item(
    payload: InventoryItemCreate,
    db: Session = Depends(get_db)
):
    """
    Commits an OCR-parsed, engineer-reviewed procurement bill item into the central inventory database.
    Assigns initial lifecycle tag (TO_BE_CONSUMED or IN_STORAGE) and updates the Knowledge Graph.
    """
    item = create_inventory_item(
        db=db,
        sku_code=payload.sku_code,
        cpse=payload.cpse,
        depot_id=payload.depot_id,
        depot_location=payload.depot_location,
        description=payload.description,
        quantity=payload.quantity,
        unit_cost_inr=payload.unit_cost_inr,
        status=payload.status.value,
        po_no=payload.po_no,
        heat_no=payload.heat_no,
        canonical_id=payload.canonical_id,
        item_type=payload.item_type,
        size_nb_mm=payload.size_nb_mm,
        pressure_class=payload.pressure_class,
        metallurgy=payload.metallurgy,
        facing_end=payload.facing_end,
        standard=payload.standard,
        source_document_id=payload.source_document_id,
        action_note=payload.action_note,
        engineer_id=payload.engineer_id,
    )

    # Sync to Neo4j Knowledge Graph
    sync_inventory_item_to_graph(
        sku_code=item.sku_code,
        cpse=item.cpse,
        depot_id=item.depot_id,
        depot_location=item.depot_location,
        description=item.description,
        canonical_id=item.canonical_id,
        quantity=item.quantity,
        unit_cost=item.unit_cost_inr,
        status=item.status,
        idle_days=item.days_idle,
    )

    # Record in audit trail
    if item.canonical_id:
        save_reconciliation_decision(
            db=db,
            source_sku=item.sku_code,
            source_cpse=item.cpse,
            matched_canonical_id=item.canonical_id,
            tier="TIER_1_IDENTICAL",
            confidence=0.95,
            verified_by_hitl=True,
            hitl_officer=payload.engineer_id,
            source_description=item.description,
            action_note=f"Inward bill committed with initial status: {payload.status.value}",
        )

    return _to_response(item)


@router.get("/items", response_model=List[InventoryItemResponse])
def list_inventory_items(
    cpse: Optional[str] = None,
    status: Optional[str] = None,
    depot_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieves plant inventory items filtered by CPSE, lifecycle status, or depot.
    """
    clean_cpse = None if (not cpse or cpse.upper() == "ALL") else cpse
    clean_status = None if (not status or status.upper() == "ALL") else status
    clean_depot = None if (not depot_id or depot_id.upper() == "ALL") else depot_id

    items = get_inventory_items(
        db=db,
        cpse=clean_cpse,
        status=clean_status,
        depot_id=clean_depot,
        limit=limit
    )
    return [_to_response(i) for i in items]


@router.get("/{item_id}", response_model=InventoryItemResponse)
def get_single_inventory_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Retrieves a single inventory item by ID."""
    item = get_inventory_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return _to_response(item)


@router.patch("/{item_id}/status", response_model=InventoryItemResponse)
def transition_item_status(
    item_id: int,
    payload: InventoryStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Transitions an item's status (e.g. TO_BE_CONSUMED -> IDLE_SURPLUS or IDLE_SURPLUS -> CONSUMED).
    When marked IDLE_SURPLUS, the item is immediately broadcasted across sister CPSEs in the Surplus Radar.
    """
    item = update_inventory_status(
        db=db,
        item_id=item_id,
        new_status=payload.status.value,
        action_note=payload.action_note,
        engineer_id=payload.engineer_id,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    # Synchronize lifecycle transition to Neo4j
    sync_inventory_item_to_graph(
        sku_code=item.sku_code,
        cpse=item.cpse,
        depot_id=item.depot_id,
        depot_location=item.depot_location,
        description=item.description,
        canonical_id=item.canonical_id,
        quantity=item.quantity,
        unit_cost=item.unit_cost_inr,
        status=item.status,
        idle_days=item.days_idle,
    )

    # Log status transition in audit ledger
    if item.canonical_id:
        save_reconciliation_decision(
            db=db,
            source_sku=item.sku_code,
            source_cpse=item.cpse,
            matched_canonical_id=item.canonical_id,
            tier="TIER_1_IDENTICAL",
            confidence=1.0,
            verified_by_hitl=True,
            hitl_officer=payload.engineer_id,
            source_description=item.description,
            action_note=f"Lifecycle transition to {payload.status.value}. Note: {payload.action_note or 'N/A'}",
        )

    return _to_response(item)
