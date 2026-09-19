from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.app.api.dependencies import get_db_session, verify_cpse_access, PaginationParams, InventoryFilterParams, validate_idempotency_key
from backend.app.services.inventory_service import list_inventory, get_item, create_item, transition_status, get_surplus_radar, get_hitl_queue

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("")
@router.get("/")
def get_inventory_list(
    filters: InventoryFilterParams = Depends(), 
    pagination: PaginationParams = Depends(), 
    cpse: str = Depends(verify_cpse_access),
    db: Session = Depends(get_db_session)
):
    filter_dict = {k: v for k, v in filters.__dict__.items() if v is not None}
    pag_dict = {"skip": pagination.skip, "limit": pagination.limit}
    return list_inventory(db, filter_dict, pag_dict, cpse)

@router.get("/surplus")
def get_surplus_items(cpse: str = Depends(verify_cpse_access), db: Session = Depends(get_db_session)):
    return get_surplus_radar(db, cpse)

@router.get("/hitl-queue")
def get_hitl_items(db: Session = Depends(get_db_session)):
    return get_hitl_queue(db)

@router.get("/{sku_code}")
def get_inventory_item(sku_code: str, cpse: str = Depends(verify_cpse_access), db: Session = Depends(get_db_session)):
    return get_item(db, sku_code, cpse)

@router.post("")
@router.post("/")
def create_inventory_item(payload: Dict[str, Any], db: Session = Depends(get_db_session)):
    return create_item(db, payload)

@router.put("/{sku_code}/status")
def update_item_status(
    sku_code: str, 
    payload: Dict[str, Any], 
    idempotency_key: str = Depends(validate_idempotency_key),
    db: Session = Depends(get_db_session)
):
    if isinstance(idempotency_key, dict) and idempotency_key.get("status") == "CACHED":
        return idempotency_key["data"]
        
    new_status = payload.get("status")
    reason = payload.get("reason", "")
    officer = payload.get("officer", "SYSTEM")
    return transition_status(db, sku_code, new_status, reason, officer)
