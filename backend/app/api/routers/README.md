# API Routers (`backend/app/api/routers/`)

This directory contains the controller endpoints of the **Samanvay-AI** REST API gateway.

---

## 1. Router-by-Router Breakdown

### `match.py` — Semantic Matching & Engineering Evaluation
- **Endpoints:**
  - `POST /api/v1/match/search`:
    - Accepts raw text requisition queries or structured attributes (item type, size NB mm, pressure class, metallurgy).
    - Executes 4-stage pipeline: (1) NFKC Dialect Normalization $\rightarrow$ (2) Candidate Retrieval from PostgreSQL / Qdrant $\rightarrow$ (3) Deterministic 21-Rule Engineering Safety Engine $\rightarrow$ (4) Continuous ML Compatibility Ranker $\rightarrow$ (5) Active Learning feedback incorporation.
    - Strictly enforces Attribute-Level Privacy by masking commercial purchase costs for cross-CPSE callers.
  - `GET /api/v1/match/benchmark`:
    - Runs automated accuracy benchmarking across the 150 public sector test cases in `datasets/golden_benchmarks.json`.

### `inventory.py` — Enterprise Inventory & Surplus Catalog
- **Endpoints:**
  - `GET /api/v1/inventory/`: Browses master catalog (5,000 authentic items) with multi-field filtering (`cpse`, `depot`, `status`, `category`) and server-side pagination (`skip`, `limit`).
  - `GET /api/v1/inventory/stats`: Returns live aggregate metrics across all CPSEs: total items, declared surplus count, HITL queue count, active requisitions count, unlocked surplus capital value (₹ Cr), and per-CPSE distribution breakdown.
  - `GET /api/v1/inventory/surplus`: Retrieves items declared as surplus across sister CPSEs with commercial purchase prices protected.
  - `GET /api/v1/inventory/hitl-queue`: Retrieves items requiring Human-In-The-Loop engineering review (unverified MTCs or $>90$ days idle).
  - `GET /api/v1/inventory/{sku_code}`: Fetches individual SKU attributes with Indian procurement specifications (BIS IS standard, OIL MESC code, GeM category, CPPP tender ref, MII class).
  - `PUT /api/v1/inventory/{sku_code}/status`: Transitions SKU status (`IDLE_SURPLUS`, `TO_BE_CONSUMED`, `ARCHIVED`) and records a cryptographically sealed event to the Sovereign Audit Ledger.

### `requisition.py` — Requisition & Order Lifecycle
- **Endpoints:**
  - `POST /api/v1/requisition/`: Creates a new inter-CPSE transfer requisition using pessimistic row-level locking to reserve candidate inventory. Supports `Idempotency-Key` header.
  - `GET /api/v1/requisition/`: Lists requisitions filtered by requesting enterprise or status (`PENDING`, `APPROVED`, `GATE_PASS_ISSUED`, `DISPATCHED`, `DELIVERED`).
  - `GET /api/v1/requisition/{req_id}`: Retrieves comprehensive requisition details, matched SKU, and transit progress.
  - `PUT /api/v1/requisition/{req_id}/approve`: Approves requisition and transitions status to `APPROVED`.
  - `PUT /api/v1/requisition/{req_id}/reject`: Declines requisition with reason.
  - `POST /api/v1/requisition/{req_id}/gatepass`: Generates Non-Returnable CISF Gate Pass with SHA-256 digital seal.
  - `PUT /api/v1/requisition/{req_id}/dispatch`: Dispatches consignment with vehicle reg, transitioning status to `DISPATCHED`.
  - `PUT /api/v1/requisition/{req_id}/deliver`: Confirms delivery at destination and triggers inventory ledger reconciliation.

### `graph.py` — Knowledge Graph Discovery & Logistics
- **Endpoints:**
  - `GET /api/v1/graph/discover`: Performs regional surplus cluster discovery and shortest road transit route calculation ($1.28\times$ tortuosity, transit hours, $CO_2$ savings) across 19 CPSE depots.
  - `GET /api/v1/graph/depot/{depot_id}`: Fetches depot details, GPS coordinates, and connected transit corridors.
  - `GET /api/v1/graph/item/{sku_code}/properties`: Traverses graph property relationships for an item.

### `audit.py` — Sovereign SHA-256 Audit Ledger
- **Endpoints:**
  - `GET /api/v1/audit/`: Paginated retrieval of immutable audit log blocks filtered by category and CPSE.
  - `GET /api/v1/audit/verify` (also `POST`): **Chain Verification Engine.** Traverses every block in the ledger from Genesis block to latest, re-hashing parent-child SHA-256 links. Returns cryptographic proof of ledger integrity.
  - `GET /api/v1/audit/export`: Exports compliance audit report in strict RFC 4180 CSV format for submission to the Comptroller and Auditor General (CAG) or Central Vigilance Commission (CVC).

### `ingest.py` — Document Vision & MTC Ingestion
- **Endpoints:**
  - `POST /api/v1/ingest/document`: Multipart PDF or image file upload.
    - Dual-path extraction: PyMuPDF digital vector stream parser (< 50ms) or PaddleOCR/EasyOCR vision on NVIDIA CUDA GPU.
    - Invokes `MTCParser` and `chemistry.py` to extract heat number, ladle chemical analysis ($\%C, \%Mn, \%Si, \%P, \%S$), IIW Carbon Equivalent ($CE_{\text{IIW}}$), PREN, and verify ASTM boundary compliance.
  - `GET /api/v1/ingest/documents`: Lists ingested document history with extraction confidence scores.
  - `GET /api/v1/ingest/documents/{doc_id}`: Retrieves full parsed metadata and raw text for an ingested document.

---

## 2. Testing Routers

```bash
# Run tests for specific router
pytest tests/api/test_inventory_api.py -v
pytest tests/api/test_match_api.py -v
pytest tests/api/test_audit_api.py -v
pytest tests/api/test_requisition_api.py -v
pytest tests/api/test_graph_api.py -v
```
