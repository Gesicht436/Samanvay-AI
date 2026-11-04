from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from backend.app.api.dependencies import _record_authorization_failure, get_db_session, require_permission
from backend.app.core import permissions as perm
from backend.app.models.tables import InventoryItem, User
from graph.logistics import (
    road_distance,
    estimate_transit_hours,
    estimate_freight_cost_inr,
    compute_co2_saved,
    DEPOT_COORDINATES,
)

router = APIRouter(prefix="/graph", tags=["Graph"])


def _session_cpse(
    current_user: User = Depends(require_permission(perm.GRAPH_READ)),
    db: Session = Depends(get_db_session),
) -> str:
    """Return the authenticated session's CPSE for read-only graph access.

    Authentication and authorization are delegated to the centralized AUTH-007
    dependency (``GRAPH_READ``). The tenant context is taken ONLY from the
    authenticated session user; a client-controlled ``X-CPSE-ID`` (or any other
    caller-supplied CPSE selector) is never consulted. If the account carries no
    CPSE, the request fails closed instead of defaulting to a fallback tenant.
    """
    cpse = current_user.cpse
    if not cpse:
        _record_authorization_failure(
            db,
            current_user,
            permission=perm.GRAPH_READ,
            reason_code="MISSING_RESOURCE_ATTRIBUTES",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "AUTHORIZATION_DENIED",
                "reason": "MISSING_RESOURCE_ATTRIBUTES",
            },
        )
    return cpse


@router.get("/discover")
def discover_surplus(
    item_type: Optional[str] = Query(default=None),
    max_distance_km: Optional[float] = Query(default=None),
    session_cpse: str = Depends(_session_cpse),
    db: Session = Depends(get_db_session),
):
    """
    Pre-Purchase Radar: surplus discovery with strict Attribute-Level Privacy.

    The tenant boundary comes ONLY from the authenticated session: the query is
    explicitly scoped to the caller's CPSE and commercial prices are never
    exposed across enterprises. ``X-CPSE-ID`` is not read.
    """
    query = db.query(InventoryItem).filter(
        InventoryItem.cpse == session_cpse,
        (InventoryItem.status == "IDLE_SURPLUS") | (InventoryItem.is_broadcasted_surplus == True),
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

        # Strict Attribute-Level Privacy: commercial prices are shown ONLY for
        # the authenticated caller's own CPSE (never a client-selected tenant).
        if item.cpse == session_cpse:
            item_dict["unit_cost_inr"] = float(item.unit_cost_inr) if item.unit_cost_inr else 0.0
            item_dict["total_value_inr"] = float(item.total_value_inr) if item.total_value_inr else 0.0

        results.append(item_dict)

    return {
        "requesting_cpse": session_cpse,
        "total_discovered": len(results),
        "items": results,
    }


@router.get("/item/{sku_code}/properties")
def get_item_properties(
    sku_code: str,
    session_cpse: str = Depends(_session_cpse),
    db: Session = Depends(get_db_session),
):
    item = db.query(InventoryItem).filter(
        InventoryItem.cpse == session_cpse,
        InventoryItem.sku_code == sku_code,
    ).first()
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
def get_depot_surplus(
    depot_id: str,
    session_cpse: str = Depends(_session_cpse),
    db: Session = Depends(get_db_session),
):
    items = db.query(InventoryItem).filter(
        InventoryItem.cpse == session_cpse,
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
def get_route_logistics(
    source_depot: str,
    target_depot: str,
    _user: User = Depends(require_permission(perm.GRAPH_READ)),
):
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


@router.get("/topology")
def get_network_topology(
    session_cpse: str = Depends(_session_cpse),
    db: Session = Depends(get_db_session),
):
    """
    Returns the caller CPSE's logistics topology including depot coordinates,
    own-CPSE inventory counts, surplus value, and active static corridors.

    The inventory aggregation is scoped at SQL level to the authenticated
    session's CPSE; no other CPSE's counts or commercial aggregates are exposed.
    """
    from sqlalchemy import func

    # 1. Own-CPSE breakdown (session-scoped at query level)
    cpse_stats = db.query(
        InventoryItem.cpse,
        func.count(InventoryItem.id).label("total_items"),
        func.count(InventoryItem.id).filter(
            (InventoryItem.status == "IDLE_SURPLUS")
            | (InventoryItem.status == "SURPLUS_DECLARED")
            | (InventoryItem.status == "POTENTIAL_SURPLUS")
            | (InventoryItem.is_broadcasted_surplus == True)
        ).label("surplus_items"),
        func.coalesce(func.sum(InventoryItem.total_value_inr), 0).label("total_value"),
    ).filter(InventoryItem.cpse == session_cpse).group_by(InventoryItem.cpse).all()

    # 2. Own-CPSE depot breakdown (session-scoped at query level)
    depot_rows = db.query(
        InventoryItem.depot_id,
        InventoryItem.depot_location,
        InventoryItem.cpse,
        func.count(InventoryItem.id).label("total_items"),
        func.count(InventoryItem.id).filter(
            (InventoryItem.status == "IDLE_SURPLUS")
            | (InventoryItem.status == "SURPLUS_DECLARED")
            | (InventoryItem.status == "POTENTIAL_SURPLUS")
            | (InventoryItem.is_broadcasted_surplus == True)
        ).label("surplus_items"),
        func.coalesce(func.sum(InventoryItem.total_value_inr), 0).label("total_value"),
    ).filter(InventoryItem.cpse == session_cpse).group_by(
        InventoryItem.depot_id, InventoryItem.depot_location, InventoryItem.cpse
    ).all()

    # Build node models
    depot_nodes = []
    for row in depot_rows:
        loc = row.depot_location or ""
        matched_coord = None
        for name, coord in DEPOT_COORDINATES.items():
            if name.lower() in loc.lower() or name.lower() in (row.depot_id or "").lower():
                matched_coord = coord
                break
        if not matched_coord:
            matched_coord = (22.3217, 73.1384)

        lat, lon = matched_coord
        svg_x = round(max(10.0, min(90.0, (lon - 68.0) / 28.0 * 75.0 + 15.0)), 1)
        svg_y = round(max(10.0, min(90.0, 100.0 - ((lat - 8.0) / 24.0 * 75.0 + 15.0))), 1)

        depot_nodes.append({
            "depot_id": row.depot_id,
            "name": f"{row.cpse} {loc.title() if loc else row.depot_id}",
            "cpse": row.cpse,
            "location": loc,
            "latitude": lat,
            "longitude": lon,
            "coords": {"x": svg_x, "y": svg_y},
            "items_count": row.total_items,
            "surplus_count": row.surplus_items,
            "unlocked_value_cr": round(float(row.total_value) / 10000000.0, 2),
        })

    # 3. Key logistics corridors
    key_corridors = [
        ("Panipat", "Visakh", "IOCL to HPCL Critical Inter-CPSE Route"),
        ("Mumbai", "Uran", "BPCL to ONGC Offshore Corridor"),
        ("Pata", "Panipat", "GAIL to IOCL Feedstock Spares Corridor"),
        ("Mathura", "Bina", "IOCL to BPCL Central Pipeline Corridor"),
        ("Koyali", "Hazira", "IOCL to ONGC West Coast Hub"),
    ]
    corridor_data = []
    for src, tgt, label in key_corridors:
        c1 = DEPOT_COORDINATES.get(src, (29.3909, 76.9635))
        c2 = DEPOT_COORDINATES.get(tgt, (17.6868, 83.2185))
        dist = road_distance(c1[0], c1[1], c2[0], c2[1])
        corridor_data.append({
            "source": src,
            "target": tgt,
            "name": label,
            "distance_km": round(dist, 1),
            "transit_hours": round(estimate_transit_hours(dist), 1),
            "co2_saved_kg": round(compute_co2_saved(dist), 1),
            "status": "OPERATIONAL",
        })

    total_val = sum(d["unlocked_value_cr"] for d in depot_nodes)
    total_itms = sum(d["items_count"] for d in depot_nodes)
    total_surplus = sum(d["surplus_count"] for d in depot_nodes)

    return {
        "network_id": "MOPNG-SOVEREIGN-MESH-01",
        "total_depots": len(depot_nodes),
        "total_items": total_itms,
        "total_surplus_items": total_surplus,
        "total_unlocked_value_cr": round(total_val, 2),
        "cpse_summary": [
            {
                "cpse": c.cpse,
                "total_items": c.total_items,
                "surplus_items": c.surplus_items,
                "total_value_cr": round(float(c.total_value) / 10000000.0, 2),
            }
            for c in cpse_stats
        ],
        "depots": depot_nodes,
        "corridors": corridor_data,
    }

