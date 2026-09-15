"""
Integration Tests for FastAPI Gateway Routes.
Tests /health, /match, /hitl, /graph, and /ingest endpoints.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
RAW_DIR = Path("data/raw")


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "Samanvay-AI" in data["service"]


def test_match_single_exact():
    payload = {
        "query": "FLG WNRF 4IN 300# A105",
        "top_k": 3
    }
    response = client.post("/api/v1/match/single", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "extracted_attributes" in data
    assert data["extracted_attributes"]["size_nb_mm"] == 100.0
    assert data["extracted_attributes"]["pressure_class"] == 300
    assert len(data["candidates"]) > 0
    primary = data["primary_match"]
    assert primary is not None
    assert primary["is_compatible"] is True


def test_hitl_queue_and_resolution():
    # 1. Fetch queue
    q_resp = client.get("/api/v1/match/hitl-queue")
    assert q_resp.status_code == 200
    queue = q_resp.json()
    assert len(queue) > 0
    first_item = queue[0]

    # 2. Resolve single item
    resolve_payload = {
        "source_sku": first_item["source_sku"],
        "source_cpse": first_item["source_cpse"],
        "canonical_id": first_item["canonical_id"],
        "decision": "APPROVE",
        "tier": first_item["tier"],
        "confidence": first_item["confidence"],
        "officer": "TEST_OFFICER",
        "action_note": "Automated verification test"
    }
    r_resp = client.post("/api/v1/match/hitl-resolve", json=resolve_payload)
    assert r_resp.status_code == 200
    assert r_resp.json()["status"] == "SUCCESS"


def test_bulk_hitl_resolve():
    bulk_payload = {
        "officer": "MAYANK_ANAND",
        "items": [
            {
                "source_sku": "IOCL-MM-TEST-1",
                "source_cpse": "IOCL",
                "canonical_id": "CAN-000009",
                "decision": "APPROVE",
                "tier": "TIER_1_IDENTICAL",
                "confidence": 0.98
            },
            {
                "source_sku": "BPCL-SAP-TEST-2",
                "source_cpse": "BPCL",
                "canonical_id": "CAN-000010",
                "decision": "APPROVE",
                "tier": "TIER_2_SUBSTITUTE",
                "confidence": 0.89
            }
        ]
    }
    resp = client.post("/api/v1/match/hitl-bulk-resolve", json=bulk_payload)
    assert resp.status_code == 200
    assert resp.json()["approved_count"] == 2


def test_graph_spares_endpoint():
    response = client.get("/api/v1/graph/spares/IOCL-MM-0000002?source_cpse=IOCL")
    assert response.status_code == 200
    data = response.json()
    assert "total_available_spares" in data
    assert "potential_capital_saved_inr" in data
    assert len(data["spares"]) > 0


def test_graph_analytics_endpoint():
    response = client.get("/api/v1/graph/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["working_capital_freed_cr"] > 0
    assert "top_surplus_depots" in data


def test_ingest_document_api():
    pdf_path = RAW_DIR / "sample_mtc_flange_01.pdf"
    assert pdf_path.exists()

    with open(pdf_path, "rb") as f:
        files = {"file": ("sample_mtc_flange_01.pdf", f, "application/pdf")}
        response = client.post("/api/v1/ingest/document", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["doc_type"] == "MTC_CERTIFICATE"
    assert data["parsed_metadata"]["cert_no"] == "MTC-2025-FLG-8819"
    assert "document_id" in data


def test_requisition_lifecycle():
    # 1. List active requisitions
    list_resp = client.get("/api/v1/requisition/list")
    assert list_resp.status_code == 200
    requisitions = list_resp.json()
    assert len(requisitions) >= 3

    # 2. Create new requisition
    create_payload = {
        "source_cpse": "IOCL",
        "source_depot": "Panipat Refinery, Haryana",
        "source_unit": "Hydrocracker Unit 3",
        "target_cpse": "ONGC",
        "target_depot": "Hazira Gas Processing Plant, Gujarat",
        "sku_code": "ONGC-MAT-0000092",
        "item_description": "FLANGE WELD NECK 4\" CL300 ASTM A105 RF",
        "required_qty": 5,
        "unit_cost_inr": 12400.0,
        "justification": "Emergency replacement during catalyst regeneration.",
        "urgency_level": "EMERGENCY_SHUTDOWN"
    }
    create_resp = client.post("/api/v1/requisition/create", json=create_payload)
    assert create_resp.status_code == 201
    created_item = create_resp.json()
    req_id = created_item["requisition_id"]
    assert created_item["status"] == "PENDING_APPROVAL"
    assert len(created_item["audit_hash"]) == 64

    # 3. Approve and issue CISF Digital Material Gate Pass
    approve_payload = {
        "approver_name": "K. R. Narayanan, GM (Materials, ONGC)",
        "vehicle_no": "HR-06-EA-9912",
        "driver_name": "Balram Singh",
        "driver_id_no": "DL-062021008129"
    }
    appr_resp = client.post(f"/api/v1/requisition/{req_id}/approve", json=approve_payload)
    assert appr_resp.status_code == 200
    approved_data = appr_resp.json()
    assert approved_data["status"] == "APPROVED_FOR_DISPATCH"
    assert approved_data["gate_pass"] is not None
    assert approved_data["gate_pass"]["gate_pass_no"].startswith("OGP-2026")
    assert "CISF-SEAL" in approved_data["gate_pass"]["cisf_verification_seal"]
    assert len(approved_data["gate_pass"]["sha256_hash"]) == 64

    # 4. Fetch official Gate Pass
    gp_resp = client.get(f"/api/v1/requisition/{req_id}/gate-pass")
    assert gp_resp.status_code == 200
    gp_data = gp_resp.json()
    assert gp_data["requisition_id"] == req_id
    assert gp_data["driver_name"] == "Balram Singh"


def test_ingest_catalog_api():
    catalog_path = Path("data/mock_cpes_catalogs/iocl_materials.csv")
    assert catalog_path.exists()

    with open(catalog_path, "rb") as f:
        files = {"file": ("iocl_materials.csv", f, "text/csv")}
        response = client.post("/api/v1/ingest/catalog?batch_size=50", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["total_items_processed"] > 0
    assert "duplicates_found" in data
    assert "safe_automated_count" in data
    assert "flagged_for_hitl" in data


def test_ingest_batch_documents_api():
    pdf_path = RAW_DIR / "sample_mtc_flange_01.pdf"
    assert pdf_path.exists()

    with open(pdf_path, "rb") as f1, open(pdf_path, "rb") as f2:
        files = [
            ("files", ("cert_1.pdf", f1, "application/pdf")),
            ("files", ("cert_2.pdf", f2, "application/pdf")),
        ]
        response = client.post("/api/v1/ingest/batch-documents", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["successful_count"] == 2
    assert len(data["documents"]) == 2


def test_ingest_documents_list_api():
    response = client.get("/api/v1/ingest/documents?limit=10")
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)

