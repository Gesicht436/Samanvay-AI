# REST API Test Suite (`tests/api/`)

This directory tests the HTTP controllers of **Samanvay-AI** using FastAPI's synchronous `TestClient` (backed by `httpx`).

---

## 1. File-by-File Breakdown

### `test_match_api.py` — Semantic Matching & Engineering Safety API Tests
- **Tests:**
  - `test_normalizer_and_matching_pipeline()`: Sends raw queries (e.g. `"VLV GT 4IN 300# WCB"`) to `POST /api/v1/match/search` and verifies extracted slots, candidate ranking, and Dynamic Compatibility Tiers.
  - `test_compatibility_ranker_scoring()`: Verifies subvector similarity score breakdowns (dimensions, metallurgy, pressure/temp, standards).

### `test_requisition_api.py` — Order Lifecycle & Concurrency Tests
- **Tests:**
  - `test_idempotency_key_behavior()`: Submits identical requisition requests with the same `Idempotency-Key` header; verifies second request returns identical response without duplicating inventory reservation.
  - `test_concurrent_lock_safety()`: Simulates concurrent requests attempting to reserve remaining inventory stock; verifies pessimistic row locking prevents over-allocation.

### `test_inventory_api.py` — Inventory & Privacy Filtering Tests
- **Tests:**
  - `test_inventory_crud_operations()`: Tests item creation, retrieval, and status updates.
  - `test_privacy_filtering()`: Verifies that when CPSE A requests an item owned by CPSE B, sensitive financial fields (`unit_price_inr`) are stripped.

### `test_graph_api.py` — Knowledge Graph & Logistics Tests
- **Tests:**
  - `test_logistics_calculation_accuracy()`: Verifies transit distance, hours, and carbon emission calculations returned by graph endpoints.
  - `test_attribute_level_privacy_stripping()`: Validates that graph surplus discovery hides proprietary pricing.

### `test_audit_api.py` — Sovereign SHA-256 Audit Ledger Tests
- **Tests:**
  - `test_audit_hash_chain_verification()`: Calls `GET /api/v1/audit/verify` and verifies that an un-tampered chain returns `is_tamper_free=True`.
  - `test_rfc_4180_csv_generation()`: Verifies that `GET /api/v1/audit/export-csv` outputs valid RFC 4180 compliant CSV formatting for statutory audit authorities.

---

## 2. Running API Tests

```bash
pytest tests/api/ -v
```
