# Datasets & Benchmark Evaluation Corpora

The `datasets` directory contains golden evaluation benchmarks, synthesized multi-tenant CPSE inventory catalogs, and OCR stress payloads used for continuous automated testing and active learning cache initialization.

---

## Dataset Inventory

### 1. `golden_benchmarks.json` (150 Paired Engineering Test Cases)
- **Record Count**: 150 paired test cases.
- **Composition**:
  - **50 Tier 1 Cases (Identical Matches)**: Exact physical and metallurgical parity ($Score \ge 0.95$).
  - **50 Tier 2 Cases (Engineering Equivalents)**: Permitted safe upgrades (e.g., Class 300 replacing Class 150, Trim 8 replacing Trim 1, 316L SS replacing 304 SS).
  - **50 Tier 3 Cases (Failure Traps)**: Deliberate violation probes testing all 21 safety modules (e.g., pressure class down-rating, flange ear fracture, missing SWG inner rings, sour service hardness violations).
- **Runtime Application**: Ingested on FastAPI application boot (`backend/main.py`) via `seed_from_golden_benchmarks` to pre-seed the in-memory active learning cache.

### 2. `inventory_catalog.csv` (Multi-CPSE Inventory Ledger)
- **Record Count**: 5,000+ material items.
- **Participating CPSEs**: IOCL, ONGC, BPCL, HPCL, GAIL, OIL, and NRL.
- **Schema**: `sku_code`, `cpse_id`, `depot_id`, `description`, `item_type`, `size_nb_mm`, `pressure_class`, `metallurgy`, `quantity`, `unit_cost_inr`, `is_surplus`, `days_idle`.
- **Seeding Target**: Used by `scripts/seed_database.py` and `backend/app/services/seeder.py` to populate PostgreSQL and Qdrant.

### 3. `ocr_payloads.json` (OCR Stress Test Suite)
- **Record Count**: 500 document payloads.
- **Purpose**: Validates OCR robustness against low-confidence scans (10% under-exposed or skewed scans) and character recognition hallucinations (5% OCR substitutions like letter 'O' for zero '0').
