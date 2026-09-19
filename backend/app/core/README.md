# Core Infrastructure, Config & Security (`backend/app/core/`)

This directory contains foundational cross-cutting components: configuration settings, exception definitions, and cryptographic security primitives.

---

## 1. File-by-File Breakdown

### `config.py` — Pydantic Settings & Environment Variables
- **Purpose:** Centralized, type-safe application configuration using `pydantic-settings`.
- **Key Classes:**
  - `Settings`:
    - `PROJECT_NAME`: `"Samanvay-AI"`
    - `VERSION`: `"2.0.0-PROD"`
    - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`, `SQLALCHEMY_DATABASE_URI`
    - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
    - `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_COLLECTION`
    - `AUDIT_GENESIS_HASH`: Cryptographic seed hash for the sovereign audit ledger.
    - `GATE_PASS_SECRET_KEY`: HMAC secret for signing digital gate passes.

### `exceptions.py` — Domain Exception Hierarchy
- **Purpose:** Translates internal domain and validation failures into standard HTTP error responses.
- **Key Exceptions:**
  - `ResourceNotFoundError(HTTPException 404)`: Raised when a requested SKU, Requisition, or Document does not exist.
  - `ValidationError(HTTPException 422)`: Raised on schema or dimensional mismatch.
  - `IdempotencyConflictError(HTTPException 409)`: Raised when an `Idempotency-Key` is reused with differing request payloads.
  - `EngineeringRuleViolationError(HTTPException 400)`: Raised when an operation violates non-negotiable safety rules (e.g. attempting to dispatch non-NACE pipe to sour service).

### `security.py` — Sovereign Cryptographic Primitives
- **Purpose:** Implements mathematical proofs of ledger immutability and anti-tamper verification.
- **Key Functions:**
  - `compute_sha256(data: str) -> str`: Standard SHA-256 cryptographic digest.
  - `compute_audit_hash(prev_hash, timestamp, actor, action, payload) -> str`:
    - Computes the chained block hash:
      $$\text{Hash}_k = \text{SHA256}(\text{Hash}_{k-1} \,\|\, t \,\|\, \text{actor} \,\|\, \text{action} \,\|\, \text{canonical\_json}(\text{payload}))$$
    - Any retroactive modification to past rows completely breaks all downstream hashes, making unauthorized tampering mathematically detectable.
  - `compute_gate_pass_seal(requisition_id, dispatch_ts, secret) -> str`:
    - Computes HMAC-SHA256 digital signature embedded on printed/electronic gate passes to prevent forged material gate releases.

---

## 2. Code Example

```python
from backend.app.core.security import compute_audit_hash, compute_gate_pass_seal

# Compute chained audit block hash
prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
block_hash = compute_audit_hash(
    prev_hash=prev_hash,
    timestamp="2026-09-19T18:00:00Z",
    actor="OFFICER_IOCL_412",
    action="REQUISITION_DISPATCH",
    payload={"req_id": "REQ-2026-001", "qty": 10}
)
print("Audit Block Hash:", block_hash)
```
