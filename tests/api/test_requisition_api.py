import pytest

def test_idempotency_key_behavior():
    processed_keys = set()
    
    def process_request(req_id, idempotency_key):
        if idempotency_key in processed_keys:
            return "ALREADY_PROCESSED"
        processed_keys.add(idempotency_key)
        return "PROCESSED"
        
    res1 = process_request("req1", "idem-123")
    res2 = process_request("req2", "idem-123")
    
    assert res1 == "PROCESSED"
    assert res2 == "ALREADY_PROCESSED"

def test_concurrent_lock_safety():
    # Mocking lock safety
    lock_acquired = False
    
    def acquire_lock():
        nonlocal lock_acquired
        if lock_acquired:
            return False
        lock_acquired = True
        return True
        
    def release_lock():
        nonlocal lock_acquired
        lock_acquired = False
        
    assert acquire_lock() is True
    assert acquire_lock() is False
    release_lock()
    assert acquire_lock() is True
