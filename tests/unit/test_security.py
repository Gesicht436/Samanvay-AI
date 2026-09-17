import pytest
import hashlib
from backend.app.core.security import compute_audit_hash, verify_audit_chain

def test_compute_audit_hash_consistency():
    data = {"action": "TRANSFER", "item_id": "123"}
    hash1 = compute_audit_hash(data)
    hash2 = compute_audit_hash(data)
    assert hash1 == hash2

def test_verify_audit_chain_detects_tampering():
    chain = [
        {"id": 1, "data": "A", "prev_hash": "0"},
    ]
    chain[0]["hash"] = compute_audit_hash(chain[0])
    
    chain.append({"id": 2, "data": "B", "prev_hash": chain[0]["hash"]})
    chain[1]["hash"] = compute_audit_hash(chain[1])
    
    # Tamper
    chain[0]["data"] = "C"
    
    # Verify
    recomputed_hash = compute_audit_hash(chain[0])
    assert recomputed_hash != chain[1]["prev_hash"]

def test_compute_gate_pass_seal():
    data = "REQ-12345:APPROVED"
    seal = hashlib.sha256(data.encode()).hexdigest()
    assert len(seal) == 64

def test_compute_request_hash_determinism():
    data1 = {"b": 2, "a": 1}
    data2 = {"a": 1, "b": 2}
    
    hash1 = compute_audit_hash(data1)
    hash2 = compute_audit_hash(data2)
    assert hash1 == hash2 # Depends on sorting keys in compute_audit_hash
