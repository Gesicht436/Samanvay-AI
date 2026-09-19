# API Routers (`backend/app/api/routers/`)

This directory contains the controller endpoints of the **Samanvay-AI** REST API.

---

## 1. Router-by-Router Breakdown

### `match.py` — Semantic Matching & Engineering Evaluation
- **Endpoints:**
  - `POST /api/v1/match/search`:
    - Accepts raw text requisition queries or structured attributes.
    - Executes 4-stage pipeline: (1) NFKC Normalization $\rightarrow$ (2) DeBERTa Slot Tagging $\rightarrow$ (3) Qdrant BGE-M3 Dense Retrieval $\rightarrow$ (4) Cross-Encoder Reranking $\rightarrow$ (5) Deterministic 21-Rule Engineering Safety Engine.
    - Returns ranked candidates with Dynamic Compatibility Tiers (1 to 4), subvector similarity radar scores, and audit violations.
  - `POST /api/v1/match/benchmark`:
    - Runs automated accuracy benchmarking across the 100+ public sector test cases in `data/golden_benchmarks.json`.

### `requisition.py` — Requisition & Order Lifecycle
- **Endpoints:**
  - `POST /api/v1/requisition/create`: Creates a new inter-CPSE requisition using pessimistic row-level locking to reserve candidate inventory. Requires `Idempotency-Key` header.
  - `GET /api/v1/requisition/list`: Lists requisitions filtered by requesting enterprise or status.
  - `GET /api/v1/requisition/{req_id}`: Retrieves comprehensive requisition details, matched SKU, and transit progress.
  - `POST /api/v1/requisition/{req_id}/approve`: Approves requisition and transitions status to `APPROVED`.
  - `POST /api/v1/requisition/{req_id}/dispatch`: Dispatches order, generates cryptographically sealed digital gate pass HMAC, and transitions status to `DISPATCHED`.

### `inventory.py` — Enterprise Inventory & Surplus Catalog
- **Endpoints:**
  - `GET /api/v1/inventory/list`: Browses inventory catalog with multi-field search and pagination.
  - `GET /api/v1/inventory/surplus`: Retrieves items identified as non-moving or surplus across all CPSEs.
  - `GET /api/v1/inventory/hitl`: Retrieves items requiring Human-In-The-Loop engineering review.
  - `GET /api/v1/inventory/items/{sku_code}`: Fetches individual SKU attributes with attribute-level privacy masking (financial purchase prices hidden across competing CPSEs).

### `graph.py` — Knowledge Graph Discovery & Logistics
- **Endpoints:**
  - `GET /api/v1/graph/discover`: Performs regional surplus cluster discovery and shortest transit route traversal across Neo4j nodes.
  - `GET /api/v1/graph/depot/{depot_id}`: Fetches depot details, coordinates, and connected transit routes.
  - `GET /api/v1/graph/item/{sku_code}`: Traverses graph relationships for an item.

### `audit.py` — Sovereign SHA-256 Audit Ledger
- **Endpoints:**
  - `GET /api/v1/audit/list`: Paginated retrieval of immutable audit log entries.
  - `GET /api/v1/audit/verify`: **Chain Verification Engine.** Traverses every block in the ledger from Genesis to the latest block, recalculating SHA-256 hashes. Returns cryptographic proof of ledger integrity.
  - `GET /api/v1/audit/export-csv`: Exports compliance audit report in strict RFC 4180 CSV format for submission to the Comptroller and Auditor General (CAG) or Central Vigilance Commission (CVC).

### `ingest.py` — Document Vision & MTC Ingestion
- **Endpoints:**
  - `POST /api/v1/ingest/upload`: Multipart PDF or image file upload.
  - Executes dual-path extraction: PyMuPDF digital stream parser or PaddleOCR vision fallback.
  - Invokes `MTCParser` and `chemistry.py` to extract heat number, chemical composition, tensile properties, and verify ASTM compliance.

---

## 2. Testing Routers

```bash
# Run tests for specific router
pytest tests/api/test_match_api.py -v
pytest tests/api/test_audit_api.py -v
pytest tests/api/test_requisition_api.py -v
```
