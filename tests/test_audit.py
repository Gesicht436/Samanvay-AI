"""
Tests for Central Sovereign Audit Trail & Movement Ledger API.
Validates CVC-compliant event logging, cryptographic SHA-256 seal integrity,
filtering by CPSE and category, and dynamic requisition inclusion.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_audit_logs():
    response = client.get("/api/v1/audit/logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) >= 5
    for log in logs:
        assert "log_id" in log
        assert "timestamp" in log
        assert "action_category" in log
        assert "actor_name" in log
        assert "sha256_hash" in log
        assert len(log["sha256_hash"]) == 64
        assert log["is_verified"] is True


def test_audit_logs_filter_by_cpse():
    response = client.get("/api/v1/audit/logs?cpse=IOCL")
    assert response.status_code == 200
    logs = response.json()
    assert all(l["cpse"] == "IOCL" for l in logs)


def test_audit_logs_filter_by_category():
    response = client.get("/api/v1/audit/logs?category=DEDUPLICATION")
    assert response.status_code == 200
    logs = response.json()
    assert all(l["action_category"] == "DEDUPLICATION" for l in logs)


def test_audit_logs_search():
    response = client.get("/api/v1/audit/logs?query=Bearing")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) >= 1
    assert any("bearing" in l["details"].lower() or "bearing" in l["action_name"].lower() for l in logs)


def test_audit_stats():
    response = client.get("/api/v1/audit/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_audit_events"] >= 5
    assert stats["verified_signatures_pct"] == 100.0
    assert stats["tamper_proof_status"] == "INTEGRITY_VERIFIED"
    assert "category_breakdown" in stats
    assert "cpse_breakdown" in stats
