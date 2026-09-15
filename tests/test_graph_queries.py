"""
Unit Tests for Cross-CPSE Spare Locator and Knowledge Graph Queries.
"""

import pytest
from backend.app.graph.queries import (
    find_inter_cpse_spares,
    link_reconciled_sku,
    get_procurement_analytics,
)


def test_find_inter_cpse_spares():
    """Test locating idle surplus spares at sister depots."""
    # Given an IOCL SKU
    spares = find_inter_cpse_spares(sku_code="IOCL-MM-0000002", source_cpse="IOCL")

    assert len(spares) > 0
    # None of the returned spares should belong to IOCL (must be ONGC or BPCL)
    for s in spares:
        assert s["owner_cpse"] != "IOCL"
        assert s["available_qty"] > 0
        assert "depot_location" in s
        assert "unit_cost" in s
        assert "total_value_inr" in s


def test_link_reconciled_sku():
    """Test persisting a reconciled material code relationship."""
    success = link_reconciled_sku(
        sku_code="IOCL-MM-0000001",
        cpse="IOCL",
        canonical_id="CAN-001407",
        tier="TIER_1_IDENTICAL",
        confidence=1.0,
        verified_by_hitl=True,
        officer="MAYANK_ANAND"
    )
    assert success is True


def test_get_procurement_analytics():
    """Test overarching procurement KPI calculations."""
    analytics = get_procurement_analytics()

    assert analytics["total_catalog_items"] >= 10000
    assert analytics["working_capital_freed_cr"] > 0
    assert analytics["duplicate_reduction_pct"] > 30.0
    assert len(analytics["top_surplus_depots"]) > 0
    assert "IOCL" in analytics["cpse_breakdown"]
    assert "ONGC" in analytics["cpse_breakdown"]
    assert "BPCL" in analytics["cpse_breakdown"]
