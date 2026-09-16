"""
API V1 Knowledge Graph and Cross-CPSE Spare Locator Routes.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from backend.app.graph.queries import (
    find_inter_cpse_spares,
    search_inter_cpse_spares,
    get_procurement_analytics,
)

router = APIRouter(prefix="/graph", tags=["Knowledge Graph & Spare Locator"])


@router.get("/discover")
def discover_inter_cpse_spares(
    query: str = Query(default="", description="Search query or specification string"),
    source_cpse: str = Query(default="ALL", description="Requesting CPSE"),
    target_cpse: str = Query(default="ALL", description="Target holding CPSE"),
    exclude_source: bool = Query(default=False, description="Whether to exclude source CPSE items"),
    limit: int = Query(default=50, ge=1, le=200)
) -> Dict[str, Any]:
    """
    Intelligent cross-CPSE spare search engine.
    Supports specifications (e.g. 10" pipe, 4" flange 300#), SKUs, or canonical IDs.
    """
    spares = search_inter_cpse_spares(
        query=query,
        source_cpse=source_cpse if source_cpse != "ALL" else None,
        target_cpse=target_cpse if target_cpse != "ALL" else None,
        exclude_source=exclude_source,
        limit=limit
    )
    total_qty = sum(s["available_qty"] for s in spares)
    total_value = sum(s["total_value_inr"] for s in spares)

    return {
        "query": query,
        "source_cpse": source_cpse,
        "target_cpse": target_cpse,
        "total_available_spares": total_qty,
        "potential_capital_saved_inr": total_value,
        "count": len(spares),
        "spares": spares
    }


@router.get("/spares/{sku_code}")
def get_inter_cpse_spares(
    sku_code: str,
    source_cpse: str = Query(default="IOCL", description="Requesting enterprise (IOCL, ONGC, BPCL)")
) -> Dict[str, Any]:
    """
    Locates matching idle stock stored across sister CPSE depots
    for the requested SKU code or search query.
    """
    spares = find_inter_cpse_spares(sku_code=sku_code, source_cpse=source_cpse)
    if not spares:
        spares = search_inter_cpse_spares(
            query=sku_code,
            source_cpse=source_cpse,
            exclude_source=True,
            limit=25
        )
    total_qty = sum(s["available_qty"] for s in spares)
    total_value = sum(s["total_value_inr"] for s in spares)

    return {
        "sku_code": sku_code,
        "requesting_cpse": source_cpse,
        "total_available_spares": total_qty,
        "potential_capital_saved_inr": total_value,
        "spares": spares
    }


@router.get("/analytics")
def get_enterprise_analytics() -> Dict[str, Any]:
    """
    Returns enterprise-wide procurement KPIs:
    - Total working capital unlocked (₹ Crores)
    - Duplicate reduction percentage
    - Depots with highest dormant surplus
    """
    return get_procurement_analytics()

