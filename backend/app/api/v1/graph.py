"""
API V1 Knowledge Graph and Cross-CPSE Spare Locator Routes.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from backend.app.graph.queries import find_inter_cpse_spares, get_procurement_analytics

router = APIRouter(prefix="/graph", tags=["Knowledge Graph & Spare Locator"])


@router.get("/spares/{sku_code}")
def get_inter_cpse_spares(
    sku_code: str,
    source_cpse: str = Query(default="IOCL", description="Requesting enterprise (IOCL, ONGC, BPCL)")
) -> Dict[str, Any]:
    """
    Locates matching idle stock stored across sister CPSE depots
    for the requested SKU code.
    """
    spares = find_inter_cpse_spares(sku_code=sku_code, source_cpse=source_cpse)
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
