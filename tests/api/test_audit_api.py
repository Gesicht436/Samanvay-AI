import pytest
import io
import csv
from backend.app.core.security import compute_audit_hash, verify_audit_chain, GENESIS_ROOT_64_HEX


def test_audit_hash_chain_verification():
    # Build a 3-block valid chain
    h1 = compute_audit_hash(
        prev_hash=GENESIS_ROOT_64_HEX,
        log_id="LOG-001",
        timestamp="2026-03-18T10:00:00Z",
        actor="OFFICER_1",
        action="INGEST_MTC",
        reference_id="MTC-001",
        details='{"standard": "ASTM A105"}',
    )
    b1 = {
        "log_id": "LOG-001",
        "timestamp": "2026-03-18T10:00:00Z",
        "actor_name": "OFFICER_1",
        "action_name": "INGEST_MTC",
        "reference_id": "MTC-001",
        "details": '{"standard": "ASTM A105"}',
        "prev_hash": GENESIS_ROOT_64_HEX,
        "sha256_hash": h1,
    }

    h2 = compute_audit_hash(
        prev_hash=h1,
        log_id="LOG-002",
        timestamp="2026-03-18T10:15:00Z",
        actor="OFFICER_2",
        action="APPROVE_REQ",
        reference_id="REQ-001",
        details='{"approved_by": "GM_STORES"}',
    )
    b2 = {
        "log_id": "LOG-002",
        "timestamp": "2026-03-18T10:15:00Z",
        "actor_name": "OFFICER_2",
        "action_name": "APPROVE_REQ",
        "reference_id": "REQ-001",
        "details": '{"approved_by": "GM_STORES"}',
        "prev_hash": h1,
        "sha256_hash": h2,
    }

    chain = [b1, b2]
    is_valid, broken_idx = verify_audit_chain(chain)
    assert is_valid is True
    assert broken_idx is None

    # Tamper with block 1 payload
    b1_tampered = b1.copy()
    b1_tampered["details"] = '{"standard": "TAMPERED"}'
    chain_tampered = [b1_tampered, b2]
    is_valid_t, broken_t = verify_audit_chain(chain_tampered)
    assert is_valid_t is False
    assert broken_t == 0


def test_rfc_4180_csv_generation():
    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM
    writer = csv.writer(output, dialect="excel")

    writer.writerow(["log_id", "actor_name", "action_name", "sha256_hash"])
    writer.writerow(["LOG-001", "cisf_officer_41", "GATE_PASS_GENERATED", "5d41402abc4b..."])

    csv_text = output.getvalue()
    assert csv_text.startswith("\ufeff")
    assert "cisf_officer_41" in csv_text
    assert "GATE_PASS_GENERATED" in csv_text
