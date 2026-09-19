# Operational & Automation Scripts (`scripts/`)

This directory contains CLI utilities, background workers, database seeders, and live integration test suites for **Samanvay-AI**.

---

## 1. File-by-File Breakdown

### `seed_database.py` — Master Database Seeder
- **Purpose:** Populates PostgreSQL tables and Qdrant vector collections from `data/inventory_catalog.csv`.
- **Key Functions:**
  - `seed_database()`: Reads 5,001 items, computes BGE-M3 dense embeddings, upserts records to Qdrant, and creates relational `InventoryItem` records in PostgreSQL.
- **Usage:**
  ```bash
  python scripts/seed_database.py
  ```

### `cdc_worker.py` — Standalone Change Data Capture Daemon
- **Purpose:** Long-running background daemon synchronizing PostgreSQL transactions to Neo4j.
- **Operation:** Continuously polls `CDCPendingEvent` rows with `status='PENDING'` every 1.0 second and replays them into Neo4j graph nodes and edges via `Neo4jSyncer`.
- **Usage:**
  ```bash
  python scripts/cdc_worker.py
  ```

### `test_live_cdc.py` — Live CDC Integration Test
- **Purpose:** Verifies that modifying inventory stock in PostgreSQL triggers immediate, automatic reflection in the Neo4j Knowledge Graph.
- **Usage:**
  ```bash
  python scripts/test_live_cdc.py
  ```

### `verify_live_api.py` — Comprehensive API Smoke Test
- **Purpose:** Tests all backend REST endpoints against a running backend instance (`http://localhost:8000`).
- **Verifications:**
  - Healthcheck (`/health`)
  - Semantic Matching (`/api/v1/match/search`)
  - Inventory Surplus Retrieval (`/api/v1/inventory/surplus`)
  - Knowledge Graph Discovery (`/api/v1/graph/discover`)
  - Cryptographic Audit Ledger Verification (`/api/v1/audit/verify`)
- **Usage:**
  ```bash
  python scripts/verify_live_api.py
  ```

### `generate_datasets.py` — Synthetic Dataset Generator
- **Purpose:** CLI script to regenerate or scale synthetic catalogs and golden benchmarks.
- **Usage:**
  ```bash
  python scripts/generate_datasets.py
  ```
