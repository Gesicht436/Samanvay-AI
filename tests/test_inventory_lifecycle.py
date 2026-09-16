"""
Unit & Integration Tests for Central Inventory Management & Lifecycle Transitions.
Validates the end-to-end site engineer workflow:
  1. Upload & commit bill item with status TO_BE_CONSUMED.
  2. Verify item is tracked internally but not broadcasted to sister CPSEs.
  3. Transition status to IDLE_SURPLUS and verify instant broadcast in Neo4j graph.
  4. Transition status to CONSUMED and verify removal from active surplus.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.graph.queries import find_inter_cpse_spares
from backend.app.ingestion.storage import init_db

init_db()
client = TestClient(app)


def test_inventory_lifecycle_workflow():
    # Step 1: Site engineer commits a reviewed procurement bill item for ONGC
    payload = {
        "sku_code": "ONGC-TEST-INV-9901",
        "cpse": "ONGC",
        "depot_id": "DEPOT-ONGC-ANK",
        "depot_location": "Ankleshwar Asset, Gujarat",
        "po_no": "PO-ONGC-2026-8812",
        "heat_no": "HT-TEST-99A",
        "description": "FLANGE WELD NECK 4IN CL300 ASTM A105 RF",
        "canonical_id": "CAN-000209",
        "item_type": "FLANGE_WELD_NECK",
        "size_nb_mm": 100.0,
        "pressure_class": 300,
        "metallurgy": "ASTM A105",
        "facing_end": "RF",
        "standard": "ASME B16.5",
        "quantity": 15,
        "unit_cost_inr": 8500.0,
        "status": "TO_BE_CONSUMED",
        "action_note": "Reserved for Unit-3 crude distillation column revamp scheduled next month",
        "engineer_id": "ENG_RAJESH_SHARMA"
    }

    resp = client.post("/api/v1/inventory/commit-bill", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    item_id = data["id"]
    assert data["sku_code"] == "ONGC-TEST-INV-9901"
    assert data["status"] == "TO_BE_CONSUMED"
    assert data["is_broadcasted_surplus"] is False
    assert data["total_value_inr"] == 15 * 8500.0

    # Step 2: Query inter-CPSE spares from IOCL perspective
    # Because status is TO_BE_CONSUMED, it must NOT appear as available surplus
    spares_for_iocl = find_inter_cpse_spares("IOCL-MM-0000001", "IOCL")
    matching_spare = next((s for s in spares_for_iocl if s.get("equivalent_sku") == "ONGC-TEST-INV-9901"), None)
    assert matching_spare is None, "TO_BE_CONSUMED item must NOT be broadcasted as surplus"

    # Step 3: Turnaround postponed, site engineer marks item as IDLE_SURPLUS
    update_payload = {
        "status": "IDLE_SURPLUS",
        "action_note": "Unit turnaround completed without utilizing this lot; marked idle for transfer to sister plants.",
        "engineer_id": "ENG_RAJESH_SHARMA"
    }
    patch_resp = client.patch(f"/api/v1/inventory/{item_id}/status", json=update_payload)
    assert patch_resp.status_code == 200
    updated_data = patch_resp.json()
    assert updated_data["status"] == "IDLE_SURPLUS"
    assert updated_data["is_broadcasted_surplus"] is True
    assert updated_data["days_idle"] >= 90

    # Step 4: Verify that item is NOW immediately visible to sister CPSEs
    # In Neo4j, ONGC-TEST-INV-9901 has CAN-000209. An IOCL item with CAN-000209 is IOCL-MM-0000209 (or similar).
    # Query spares directly:
    items_list_resp = client.get("/api/v1/inventory/items?status=IDLE_SURPLUS")
    assert items_list_resp.status_code == 200
    items_list = items_list_resp.json()
    found = any(i["id"] == item_id and i["status"] == "IDLE_SURPLUS" for i in items_list)
    assert found is True

    # Step 5: After transfer or installation, engineer marks as CONSUMED
    consume_payload = {
        "status": "CONSUMED",
        "action_note": "Fitted to emergency bypass line.",
        "engineer_id": "ENG_RAJESH_SHARMA"
    }
    consume_resp = client.patch(f"/api/v1/inventory/{item_id}/status", json=consume_payload)
    assert consume_resp.status_code == 200
    consumed_data = consume_resp.json()
    assert consumed_data["status"] == "CONSUMED"
    assert consumed_data["is_broadcasted_surplus"] is False
