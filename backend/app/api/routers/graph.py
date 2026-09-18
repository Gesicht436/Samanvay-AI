from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from backend.app.api.dependencies import get_db_session
from backend.app.models.tables import InventoryItem
from graph.logistics import (
    road_distance,
    estimate_transit_hours,
    estimate_freight_cost_inr,
    compute_co2_saved,
    DEPOT_COORDINATES,
)

router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get("/discover")
def discover_surplus(
    item_type: Optional[str] = Query(default=None),
    max_distance_km: Optional[float] = Query(default=None),
    x_cpse: Optional[str] = Header(default="IOCL", alias="X-CPSE-ID"),
    db: Session = Depends(get_db_session),
):
    """
    Pre-Purchase Radar: Cross-CPSE surplus discovery with strict Attribute-Level Privacy.
    Commercial prices are strictly stripped across enterprises.
    """
    query = db.query(InventoryItem).filter(
        (InventoryItem.status == "IDLE_SURPLUS") | (InventoryItem.is_broadcasted_surplus == True)
    )

    if item_type and item_type != "ALL":
        query = query.filter(InventoryItem.item_type == item_type)

    surplus_items = query.limit(50).all()

    # Source coordinate (caller depot)
    source_coord = DEPOT_COORDINATES.get("Panipat", (29.3909, 76.9635))

    results = []
    for item in surplus_items:
        # Determine depot coordinates
        target_depot = item.depot_location or item.depot_id or "Panipat"
        matched_coord = None
        for name, coord in DEPOT_COORDINATES.items():
            if name.lower() in target_depot.lower():
                matched_coord = coord
                break
        if not matched_coord:
            matched_coord = (22.3217, 73.1384)  # Default central India

        dist = road_distance(source_coord[0], source_coord[1], matched_coord[0], matched_coord[1])
        if max_distance_km and dist > max_distance_km:
            continue

        transit_hrs = estimate_transit_hours(dist)
        co2_saved = compute_co2_saved(dist)

        item_dict = {
            "id": f"SP-{item.id}",
            "sku_code": item.sku_code,
            "cpse": item.cpse,
            "depot_id": item.depot_id,
            "depot_location": item.depot_location,
            "description": item.description,
            "item_type": item.item_type,
            "size_nb_mm": float(item.size_nb_mm) if item.size_nb_mm else None,
            "pressure_class": item.pressure_class,
            "schedule": item.schedule,
            "metallurgy": item.metallurgy,
            "facing_end": item.facing_end,
            "standard": item.standard,
            "available_quantity": item.quantity,
            "days_idle": item.days_idle,
            "distance_km": round(dist, 1),
            "transit_hours": round(transit_hrs, 1),
            "co2_saved_kg": round(co2_saved, 1),
        }

        # Strict Attribute-Level Privacy: commercial prices shown ONLY if caller is same CPSE
        if item.cpse == x_cpse:
            item_dict["unit_cost_inr"] = float(item.unit_cost_inr) if item.unit_cost_inr else 0.0
            item_dict["total_value_inr"] = float(item.total_value_inr) if item.total_value_inr else 0.0

        results.append(item_dict)

    return {
        "requesting_cpse": x_cpse,
        "total_discovered": len(results),
        "items": results,
    }


@router.get("/item/{sku_code}/properties")
def get_item_properties(sku_code: str, db: Session = Depends(get_db_session)):
    item = db.query(InventoryItem).filter(InventoryItem.sku_code == sku_code).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Part SKU {sku_code} not found")

    return {
        "sku_code": item.sku_code,
        "cpse": item.cpse,
        "canonical_id": item.canonical_id,
        "properties": {
            "item_type": item.item_type,
            "size_nb_mm": float(item.size_nb_mm) if item.size_nb_mm else None,
            "pressure_class": item.pressure_class,
            "schedule": item.schedule,
            "metallurgy": item.metallurgy,
            "facing_end": item.facing_end,
            "standard": item.standard,
            "heat_no": item.heat_no,
            "extended_properties": item.properties or {},
        },
    }


@router.get("/depot/{depot_id}/surplus")
def get_depot_surplus(depot_id: str, db: Session = Depends(get_db_session)):
    items = db.query(InventoryItem).filter(
        InventoryItem.depot_id == depot_id,
        (InventoryItem.status == "IDLE_SURPLUS") | (InventoryItem.is_broadcasted_surplus == True),
    ).all()
    return {
        "depot_id": depot_id,
        "surplus_count": len(items),
        "items": [
            {
                "sku_code": i.sku_code,
                "description": i.description,
                "item_type": i.item_type,
                "quantity": i.quantity,
                "days_idle": i.days_idle,
            }
            for i in items
        ],
    }


@router.get("/logistics/{source_depot}/{target_depot}")
def get_route_logistics(source_depot: str, target_depot: str):
    # Lookup coordinates
    coord1 = None
    coord2 = None

    for name, c in DEPOT_COORDINATES.items():
        if name.lower() in source_depot.lower():
            coord1 = c
        if name.lower() in target_depot.lower():
            coord2 = c

    if not coord1:
        coord1 = DEPOT_COORDINATES.get("Panipat", (29.3909, 76.9635))
    if not coord2:
        coord2 = DEPOT_COORDINATES.get("Visakh", (17.6868, 83.2185))

    dist = road_distance(coord1[0], coord1[1], coord2[0], coord2[1])
    hrs = estimate_transit_hours(dist)
    co2 = compute_co2_saved(dist)
    freight = estimate_freight_cost_inr(dist, 1000.0)  # 1 ton benchmark

    return {
        "source": source_depot,
        "target": target_depot,
        "distance_km": round(dist, 1),
        "transit_hours": round(hrs, 1),
        "co2_saved_kg": round(co2, 1),
        "estimated_freight_inr": round(freight, 2),
    }
