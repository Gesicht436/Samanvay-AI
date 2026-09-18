import pytest
from backend.app.core.security import (
    compute_audit_hash,
    compute_request_hash,
    compute_gate_pass_seal,
    verify_audit_chain,
    GENESIS_ROOT_64_HEX,
)


def test_compute_audit_hash_consistency():
    hash1 = compute_audit_hash(
        prev_hash=GENESIS_ROOT_64_HEX,
        log_id="LOG-001",
        timestamp="2026-09-18T10:00:00Z",
        actor="IOCL_OFFICER",
        action="TRANSFER",
        reference_id="REQ-123",
        details="Transferred 50 units",
    )
    hash2 = compute_audit_hash(
        prev_hash=GENESIS_ROOT_64_HEX,
        log_id="LOG-001",
        timestamp="2026-09-18T10:00:00Z",
        actor="IOCL_OFFICER",
        action="TRANSFER",
        reference_id="REQ-123",
        details="Transferred 50 units",
    )
    assert hash1 == hash2
    assert len(hash1) == 64


def test_verify_audit_chain_detects_tampering():
    h0 = compute_audit_hash(
        prev_hash=GENESIS_ROOT_64_HEX,
        log_id="LOG-001",
        timestamp="2026-09-18T10:00:00Z",
        actor="IOCL_OFFICER",
        action="CREATE",
        reference_id="REQ-1",
        details="Created req",
    )
    entry1 = {
        "log_id": "LOG-001",
        "timestamp": "2026-09-18T10:00:00Z",
        "actor_name": "IOCL_OFFICER",
        "action_name": "CREATE",
        "reference_id": "REQ-1",
        "details": "Created req",
        "prev_hash": GENESIS_ROOT_64_HEX,
        "sha256_hash": h0,
    }

    h1 = compute_audit_hash(
        prev_hash=h0,
        log_id="LOG-002",
        timestamp="2026-09-18T10:05:00Z",
        actor="HPCL_OFFICER",
        action="APPROVE",
        reference_id="REQ-1",
        details="Approved req",
    )
    entry2 = {
        "log_id": "LOG-002",
        "timestamp": "2026-09-18T10:05:00Z",
        "actor_name": "HPCL_OFFICER",
        "action_name": "APPROVE",
        "reference_id": "REQ-1",
        "details": "Approved req",
        "prev_hash": h0,
        "sha256_hash": h1,
    }

    # Valid chain
    is_valid, broken_idx = verify_audit_chain([entry1, entry2])
    assert is_valid is True
    assert broken_idx is None

    # Tamper with first entry
    tampered_entry1 = dict(entry1)
    tampered_entry1["details"] = "Tampered details"
    is_valid_tampered, broken_idx_tampered = verify_audit_chain([tampered_entry1, entry2])
    assert is_valid_tampered is False
    assert broken_idx_tampered == 0


def test_compute_gate_pass_seal():
    seal = compute_gate_pass_seal(
        gate_pass_no="OGP-2026-PAN-081-0001",
        vehicle_no="HR-06-AA-1234",
        driver_id="DL-88219482",
        sku_code="IOCL-FLG-001",
        quantity=25,
        issuing_officer="SR_SECURITY_OFFICER",
        timestamp="2026-09-18T12:00:00Z",
    )
    assert len(seal) == 64


def test_compute_request_hash_determinism():
    data1 = {"b": 2, "a": 1}
    data2 = {"a": 1, "b": 2}
    hash1 = compute_request_hash(data1)
    hash2 = compute_request_hash(data2)
    assert hash1 == hash2
    assert len(hash1) == 64
