# Dataset & Dialect Generators (`datasets/generators/`)

This directory contains procedural generation scripts that simulate multi-CPSE inventory catalogs, realistic ERP dialect variations, and golden evaluation benchmarks.

---

## 1. File Breakdown

### `generate_datasets.py` — Procedural Multi-Enterprise Generator (676 lines)
- **Purpose:** Generates realistic, physically valid mechanical engineering records across various CPSE ERP dialects.
- **Key Functions:**
  - `generate_iocl_description(item_type, size, cls, mat, sched, facing, trim, is_sparse)`:
    - Simulates legacy IOCL refinery ERP records.
    - Uses compact abbreviations (`"VLV GT"`, `"300#"`, `"WCB"`, `"TR8"`).
  - `generate_ongc_description(item_type, size, cls, mat, sched, facing, trim, is_sparse)`:
    - Simulates ONGC offshore exploration records.
    - Uses structured comma-delimited syntax with NACE sour service designations.
  - `generate_metric_description(item_type, size, cls, mat, sched, facing, trim, is_sparse)`:
    - Simulates modern SAP S/4HANA instances using metric sizing (`DN50`, `DN100`, `PN50`, `PN100`).
  - `generate_catalog(num_records)`:
    - Samples physically consistent equipment combinations (e.g. ensures valve pressure classes align with standard ASME ratings, matches pipe schedules to nominal diameters).
    - Allocates inventory across 5 enterprises and 15 physical depot locations across India.
  - `generate_golden_benchmarks()`:
    - Generates 100+ mathematically and mechanically verified test cases covering all 4 Dynamic Compatibility Tiers.

---

## 2. Usage

```bash
# Generate default 5,000 item catalog and golden benchmarks
python datasets/generators/generate_datasets.py
```
