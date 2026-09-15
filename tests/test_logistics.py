"""
Comprehensive Tests for GIS Logistics Routing, QR Gate Passes, and Real-time Inventory Reservation.
Verifies MoPNG Inter-CPSE Material Transfers across IOCL, ONGC, and BPCL.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.matching.logistics import (
    DEPOT_REGISTRY,
    resolve_depot,
    haversine_distance_km,
    estimate_route,
    generate_gate_pass_qr_code,
)

client = TestClient(app)


def test_depot_resolution_and_haversine():
    # 1. Exact depot match
    pnp = resolve_depot("IOCL-PNP")
    assert pnp is not None
    assert pnp.state == "Haryana"
    assert pnp.cpse == "IOCL"

    hzr = resolve_depot("Hazira Gas Processing Plant, Gujarat")
    assert hzr is not None
    assert hzr.cpse == "ONGC"
    assert hzr.state == "Gujarat"

    # 2. Haversine distance
    dist = haversine_distance_km(pnp.latitude, pnp.longitude, hzr.latitude, hzr.longitude)
    assert 900.0 < dist < 1200.0


def test_route_estimator():
    # Panipat to Hazira
    route = estimate_route("Panipat", "Hazira", cargo_weight_tons=2.5)
    assert route["road_distance_km"] > 1000.0
    assert route["total_transit_hours"] > 25
    assert route["freight_cost_inr"] > 40000.0
    assert route["co2_avoided_vs_import_kg"] > 1000.0
    assert "North-South" in route["primary_corridor"] or "Western" in route["primary_corridor"] or "IOCL" in route["primary_corridor"]

    # Mumbai to Mathura
    route2 = estimate_route("Mumbai Refinery, Mahul", "Mathura Refinery", cargo_weight_tons=1.0)
    assert route2["road_distance_km"] > 1000.0
    assert route2["freight_cost_inr"] > 30000.0


def test_qr_code_generation():
    payload = "OGP-2026-HZR-081-0092|IND-2026-0042|HR-06-EA-8841"
    svg_str, data_url = generate_gate_pass_qr_code(payload)
    assert "<svg" in svg_str
    assert "</svg>" in svg_str
    assert data_url.startswith("data:image/svg+xml;base64,")


def test_api_list_depots():
    resp = client.get("/api/v1/requisition/depots")
    assert resp.status_code == 200
    depots = resp.json()
    assert len(depots) >= 10
    cpse_set = {d["cpse"] for d in depots}
    assert "IOCL" in cpse_set
    assert "ONGC" in cpse_set
    assert "BPCL" in cpse_set


def test_api_route_estimate():
    payload = {
        "origin_depot": "Hazira Gas Processing Plant, Gujarat",
        "destination_depot": "Panipat Refinery, Haryana",
        "cargo_weight_tons": 1.5
    }
    resp = client.post("/api/v1/requisition/route-estimate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["road_distance_km"] > 1000.0
    assert data["freight_cost_inr"] > 40000.0
    assert data["total_transit_hours"] > 20


def test_api_inventory_locks():
    resp = client.get("/api/v1/requisition/inventory-locks")
    assert resp.status_code == 200
    locks = resp.json()
    assert len(locks) >= 3
    # Check that reserved quantities are reflected
    hzr_item = next((item for item in locks if item["sku_code"] == "ONGC-MAT-0000092"), None)
    assert hzr_item is not None
    assert hzr_item["reserved_stock"] >= 15
    assert hzr_item["lock_status"] in ["PARTIALLY_RESERVED", "LOCKED"]


def test_requisition_lifecycle_with_reservation_and_qr():
    # 1. Check initial inventory for Koyali bearing
    resp_init = client.get("/api/v1/requisition/inventory-locks")
    initial_locks = {item["sku_code"]: item for item in resp_init.json()}
    koyali_avail = initial_locks["IOCL-SAP-0004120"]["available_stock"]

    # 2. Create Requisition
    create_payload = {
        "source_cpse": "BPCL",
        "source_depot": "Mumbai Refinery, Mahul, Maharashtra",
        "source_unit": "Lube Blending Plant",
        "target_cpse": "IOCL",
        "target_depot": "Gujarat Refinery (Koyali), Vadodara",
        "sku_code": "IOCL-SAP-0004120",
        "item_description": "BEARING DEEP GROOVE BALL 50X110X27MM C3 CLEARANCE SKF ISO 15 (6310-2RS1/C3)",
        "required_qty": 5,
        "unit_cost_inr": 14200.0,
        "justification": "Urgent bearing replacement for high pressure feed pump.",
        "urgency_level": "EMERGENCY_SHUTDOWN"
    }
    create_resp = client.post("/api/v1/requisition/create", json=create_payload)
    assert create_resp.status_code == 201
    created_req = create_resp.json()
    req_id = created_req["requisition_id"]
    assert created_req["status"] == "PENDING_APPROVAL"

    # Verify inventory was reserved atomically
    resp_locked = client.get("/api/v1/requisition/inventory-locks")
    locked_locks = {item["sku_code"]: item for item in resp_locked.json()}
    assert locked_locks["IOCL-SAP-0004120"]["available_stock"] == koyali_avail - 5
    assert locked_locks["IOCL-SAP-0004120"]["reserved_stock"] == 5

    # 3. Approve and issue gate pass with QR code
    approve_payload = {
        "approver_name": "K. S. Verma, CGM (Materials, IOCL)",
        "vehicle_no": "GJ-06-ZZ-4192",
        "driver_name": "Mahesh Patel",
        "driver_id_no": "DL-061998412891"
    }
    appr_resp = client.post(f"/api/v1/requisition/{req_id}/approve", json=approve_payload)
    assert appr_resp.status_code == 200
    approved_req = appr_resp.json()
    assert approved_req["status"] == "APPROVED_FOR_DISPATCH"
    gp = approved_req["gate_pass"]
    assert gp is not None
    assert gp["qr_code_svg"] is not None
    assert "<svg" in gp["qr_code_svg"]
    assert gp["qr_code_data_url"].startswith("data:image/svg+xml;base64,")
    assert gp["transit_distance_km"] > 350.0  # Vadodara to Mumbai is ~410 km

    # 4. Verify gate pass via public CISF checkpoint endpoint
    verify_resp = client.get(f"/api/v1/requisition/gate-pass/{gp['gate_pass_no']}/verify")
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["is_valid"] is True
    assert verify_data["cisf_seal_valid"] is True
    assert verify_data["gate_pass_no"] == gp["gate_pass_no"]
    assert "AUTHENTICATED" in verify_data["verification_message"]

    # 5. Dispatch vehicle at origin refinery gate
    dispatch_resp = client.post(f"/api/v1/requisition/{req_id}/dispatch")
    assert dispatch_resp.status_code == 200
    dispatched_req = dispatch_resp.json()
    assert dispatched_req["status"] == "IN_TRANSIT"
    assert dispatched_req["dispatch_timestamp"] is not None

    # 6. Receive vehicle at destination refinery bay
    deliver_resp = client.post(f"/api/v1/requisition/{req_id}/deliver")
    assert deliver_resp.status_code == 200
    delivered_req = deliver_resp.json()
    assert delivered_req["status"] == "DELIVERED"
    assert delivered_req["delivery_timestamp"] is not None


def test_rejection_releases_inventory_lock():
    # 1. Create requisition for rejection test
    create_payload = {
        "source_cpse": "IOCL",
        "source_depot": "Mathura Refinery, Uttar Pradesh",
        "target_cpse": "BPCL",
        "target_depot": "Mumbai Refinery, Mahul, Maharashtra",
        "sku_code": "BPCL-SAP-0008891",
        "item_description": "SEAL MECHANICAL 50MM CARTRIDGE DUAL PRESSURIZED PLAN 53A SIC/SIC API 682",
        "required_qty": 3,
        "unit_cost_inr": 92000.0,
        "justification": "Test requisition for rejection workflow.",
        "urgency_level": "ROUTINE"
    }
    create_resp = client.post("/api/v1/requisition/create", json=create_payload)
    assert create_resp.status_code == 201
    req_id = create_resp.json()["requisition_id"]

    # Verify 3 units reserved
    resp_before = client.get("/api/v1/requisition/inventory-locks")
    lock_before = next(item for item in resp_before.json() if item["sku_code"] == "BPCL-SAP-0008891")
    assert lock_before["reserved_stock"] == 3

    # 2. Reject requisition
    reject_payload = {
        "rejection_reason": "Material reserved for unit CDU-1 annual maintenance.",
        "rejected_by": "R. Ramanathan, Chief Manager (Stores)"
    }
    reject_resp = client.post(f"/api/v1/requisition/{req_id}/reject", json=reject_payload)
    assert reject_resp.status_code == 200
    rejected_req = reject_resp.json()
    assert rejected_req["status"] == "REJECTED"
    assert rejected_req["rejection_reason"] == reject_payload["rejection_reason"]

    # Verify inventory was restored back to available
    resp_after = client.get("/api/v1/requisition/inventory-locks")
    lock_after = next(item for item in resp_after.json() if item["sku_code"] == "BPCL-SAP-0008891")
    assert lock_after["reserved_stock"] == 0
    assert lock_after["available_stock"] == lock_before["available_stock"] + 3
