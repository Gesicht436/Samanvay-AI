import pytest
from graph.logistics import (
    road_distance,
    estimate_transit_hours,
    estimate_freight_cost_inr,
    compute_co2_saved,
    DEPOT_COORDINATES,
)


def test_logistics_calculation_accuracy():
    pnp = DEPOT_COORDINATES["Panipat"]
    visakh = DEPOT_COORDINATES["Visakh"]

    dist = road_distance(pnp[0], pnp[1], visakh[0], visakh[1])
    assert dist > 1200.0  # ~1700 km road distance
    assert dist < 2500.0

    transit_hrs = estimate_transit_hours(dist)
    assert transit_hrs > 24.0

    freight_inr = estimate_freight_cost_inr(dist, 2000.0)  # 2 tons
    assert freight_inr > 5000.0

    co2_saved = compute_co2_saved(dist)
    assert isinstance(co2_saved, float)


def test_attribute_level_privacy_stripping():
    sample_inventory_record = {
        "sku_code": "PRT-8892",
        "cpse": "IOCL",
        "depot_id": "IOCL-PNP",
        "description": "Weld Neck Flange 4in",
        "unit_cost_inr": 12500.00,
        "total_value_inr": 150000.00,
        "po_no": "PO-IOCL-2024-991",
        "quantity": 12,
    }

    # Caller from ONGC (cross-CPSE)
    requesting_cpse = "ONGC"
    filtered = sample_inventory_record.copy()
    if filtered["cpse"] != requesting_cpse:
        filtered.pop("unit_cost_inr", None)
        filtered.pop("total_value_inr", None)
        filtered.pop("po_no", None)

    assert "unit_cost_inr" not in filtered
    assert "total_value_inr" not in filtered
    assert "po_no" not in filtered
    assert filtered["sku_code"] == "PRT-8892"
    assert filtered["quantity"] == 12

    # Caller from same CPSE (IOCL)
    same_filtered = sample_inventory_record.copy()
    if same_filtered["cpse"] != "IOCL":
        same_filtered.pop("unit_cost_inr", None)

    assert "unit_cost_inr" in same_filtered
