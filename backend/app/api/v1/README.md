# Version 1 API Reference (`backend/app/api/v1`)

## 1. Overview
The `api/v1` directory implements all RESTful API endpoints in Samanvay-AI. It exposes endpoints for material matching, human-in-the-loop triage, document intake, cross-CPSE requisition logistics, graph traversal, and audit logging.

---

## 2. Router Modules Overview

| Router File | URL Prefix | Purpose |
|---|---|---|
| `match.py` | `/api/v1/match` | Single-item matching, ASME safety verification, HITL triage, and active learning cache. |
| `requisition.py` | `/api/v1/requisition` | Inter-CPSE material transfer requisitions, inventory locks, GIS logistics, and CISF gate passes. |
| `ingest.py` | `/api/v1/ingest` | Multi-modal OCR document intake and batch invoice processing. |
| `graph.py` | `/api/v1/graph` | Knowledge graph exploration, taxonomy navigation, and surplus spare radar. |
| `audit.py` | `/api/v1/audit` | Chronological audit ledger, SHA-256 integrity verification, and compliance metrics. |

---

## 3. Detailed Endpoint Specification

### A. Material Matching & HITL Triage (`/api/v1/match`)

#### 1. Single Item Standardization & Verification
- Endpoint: `POST /api/v1/match/single`
- Description: Extracts engineering attributes from raw procurement text, retrieves candidate SKUs from Qdrant, verifies deterministic ASME/ASTM rules, and applies active learning reranking.
- Request Body:
  ```json
  {
    "query": "FLG WNRF 4IN 300# A105",
    "top_k": 5
  }
  ```
- Response (200 OK):
  ```json
  {
    "query": "FLG WNRF 4IN 300# A105",
    "extracted_attributes": {
      "item_type": "FLANGE_WELD_NECK",
      "size_nb_mm": 100.0,
      "size_inch": "4\"",
      "pressure_class": 300,
      "metallurgy": "ASTM A105",
      "facing_end": "RF",
      "standard": "ASME B16.5"
    },
    "total_candidates": 5,
    "primary_match": {
      "tier": "TIER_1_IDENTICAL",
      "is_compatible": true,
      "confidence_score": 1.0,
      "canonical_id": "CAN-000009",
      "rationale": "ACCEPT (Tier-1 Identical): 100% specification parity across size, rating, metallurgy, and mating interfaces."
    },
    "candidates": [...]
  }
  ```

#### 2. Get Pending HITL Triage Queue
- Endpoint: `GET /api/v1/match/hitl-queue?limit=25`
- Description: Retrieves pending ambiguous matches and Tier-2 upgrades requiring human review.
- Response (200 OK): Returns array of queue items with source vs candidate parameter breakdowns.

#### 3. Resolve Single HITL Item
- Endpoint: `POST /api/v1/match/hitl-resolve`
- Description: Records an engineer approval, rejection, or reclassification, logs audit trail, and updates active learning cache.
- Request Body:
  ```json
  {
    "source_sku": "IOCL-MM-0004128",
    "source_cpse": "IOCL",
    "canonical_id": "CAN-000009",
    "decision": "APPROVE",
    "tier": "TIER_1_IDENTICAL",
    "confidence": 0.98,
    "officer": "MAYANK_ANAND",
    "action_note": "Verified 100% specification parity on Unit-3 heater line."
  }
  ```

#### 4. Batch HITL Bulk Resolution
- Endpoint: `POST /api/v1/match/hitl-bulk-resolve`
- Description: 1-click batch approval of multiple safe verified matches.

#### 5. Active Learning Feedback Cache & Stats
- Endpoint: `GET /api/v1/match/feedback-cache`
- Description: Retrieves active learning cache statistics, total human overrides, and historical verification records.

---

### B. Inter-CPSE Requisition & Logistics (`/api/v1/requisition`)

#### 1. Create Transfer Requisition
- Endpoint: `POST /api/v1/requisition/create`
- Description: Initiates an inter-depot transfer, computes GIS road distance, locks surplus inventory atomically, and creates an audit record.
- Request Body:
  ```json
  {
    "source_cpse": "IOCL",
    "source_depot": "Panipat Refinery, Haryana",
    "target_cpse": "ONGC",
    "target_depot": "Hazira Gas Processing Plant, Gujarat",
    "material_name": "Weld Neck Flange 4\" Class 300 RF A105",
    "requested_qty": 10,
    "unit_rate_inr": 12400,
    "urgency": "EMERGENCY_SHUTDOWN",
    "justification": "Unit-3 Hydrocracker turnaround requirement."
  }
  ```
- Response (200 OK): Returns requisition record with calculated road distance, estimated freight cost, and transit days.

#### 2. List Requisitions
- Endpoint: `GET /api/v1/requisition/list`
- Description: Lists all active transfer requisitions with status filtering.

#### 3. View Inventory Reservation Locks
- Endpoint: `GET /api/v1/requisition/inventory-locks`
- Description: Returns active multi-depot inventory reservation locks preventing double-allocation.

#### 4. Update Requisition Lifecycle State
- Endpoint: `POST /api/v1/requisition/{req_id}/action`
- Description: Advances status through: `APPROVED`, `DISPATCHED`, `DELIVERED`, `CANCELLED`.

#### 5. Issue Official Digital CISF Gate Pass
- Endpoint: `GET /api/v1/requisition/{req_id}/gate-pass`
- Description: Generates a printable CISF Material Gate Pass with scannable SVG QR code and SHA-256 seal.

#### 6. Calculate GIS Haversine Depot Distance
- Endpoint: `POST /api/v1/requisition/calculate-distance`
- Description: Computes distance in kilometers, estimated transit duration, and road freight between any two CPSE depots.

---

### C. Multi-Modal Document & MTC Ingestion (`/api/v1/ingest`)

#### 1. Ingest Single Document / Image
- Endpoint: `POST /api/v1/ingest/document`
- Description: Accepts file upload (PDF or JPEG/PNG image), applies Windows Media OCR (`winocr`) or PaddleOCR, and extracts structured items and chemical/mechanical properties.

#### 2. Ingest Batch Documents
- Endpoint: `POST /api/v1/ingest/batch-documents`
- Description: Uploads multiple invoices or certificates simultaneously, processing them in parallel.

---

### D. Knowledge Graph & Ontology (`/api/v1/graph`)

#### 1. Retrieve Graph Ontology Summary
- Endpoint: `GET /api/v1/graph/ontology`
- Description: Returns total canonical items, CPSE SKU nodes, depot relationships, and taxonomic linkages.

#### 2. Cross-CPSE Surplus Inventory Radar
- Endpoint: `GET /api/v1/graph/surplus-radar?canonical_id=CAN-000001`
- Description: Discovers all matching inventory holdings across IOCL, ONGC, and BPCL depots for a given canonical item.

---

### E. Sovereign Audit Trail Ledger (`/api/v1/audit`)

#### 1. Get Audit Ledger
- Endpoint: `GET /api/v1/audit/ledger?limit=100`
- Description: Returns chronological compliance events with SHA-256 tamper-evident digital seals.

#### 2. Verify Audit Record Integrity
- Endpoint: `GET /api/v1/audit/verify/{audit_id}`
- Description: Recomputes the SHA-256 cryptographic hash over event parameters to verify that the audit log has not been modified.
