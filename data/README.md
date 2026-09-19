# Data Repository & Catalogs (`data/`)

This directory houses the foundational datasets, benchmarks, and OCR test payloads powering **Samanvay-AI**.

---

## 1. File-by-File Breakdown

### `inventory_catalog.csv` — Multi-CPSE Master Inventory Catalog (5,001 Items)
- **Purpose:** Realistic, synthetically generated yet strictly standardized enterprise catalog modeling stock across India's 5 major public sector oil & gas enterprises (**IOCL, ONGC, GAIL, BPCL, HPCL**).
- **Columns:**
  - `sku_code`: Unique identifier (e.g. `IOCL-PR-VLV-0001`, `ONGC-HZ-PIP-0042`).
  - `cpse`: Owning enterprise (`IOCL`, `ONGC`, `GAIL`, `BPCL`, `HPCL`).
  - `plant_name`: Specific facility (e.g. `Paradip Refinery`, `Hazira Gas Complex`, `Jamnagar Terminal`, `Mathura Refinery`).
  - `depot_location`: Regional warehouse code.
  - `item_type`: Equipment taxonomy (`GATE_VALVE`, `GLOBE_VALVE`, `BALL_VALVE`, `CHECK_VALVE`, `PIPE`, `FLANGE`, `FITTING`, `PUMP`, `MOTOR`, `GASKET`).
  - `nominal_size`: Diameter spec (`0.5 INCH` to `48 INCH`, `DN15` to `DN1200`).
  - `pressure_class`: ASME B16.5 rating (`150`, `300`, `600`, `900`, `1500`, `2500`).
  - `material_grade`: ASTM metallurgical standard (`ASTM A105`, `ASTM A106 Gr B`, `ASTM A216 WCB`, `ASTM A350 LF2`, `ASTM A182 F316L`, `ASTM A182 F51 Duplex`).
  - `schedule`: Pipe wall schedule (`SCH 40`, `SCH 80`, `SCH 160`, `STD`, `XS`, `XXS`).
  - `facing`: Flange face (`RF`, `RTJ`, `FF`).
  - `trim`: API valve trim (`TRIM 1`, `TRIM 5`, `TRIM 8`, `TRIM 10`).
  - `quantity_on_hand`: Physical count stored in warehouse.
  - `quantity_reserved`: Units locked for active requisitions.
  - `unit_of_measure`: `EA` (Each), `MTR` (Meters).
  - `unit_price_inr`: Book inventory value (treated as sovereign confidential; masked across CPSE boundaries).
  - `is_surplus`: Boolean flag indicating non-moving idle surplus eligible for inter-plant pooling.
  - `description`: Realistic raw ERP line item description with simulated dialect noise.

### `golden_benchmarks.json` — Verified Engineering Inter-Change Benchmarks (100+ Cases)
- **Purpose:** Curated ground-truth test suite verifying matching accuracy across all 4 Dynamic Compatibility Tiers.
- **Structure per Case:**
  - `case_id`: e.g. `GB-VLV-001`.
  - `query_description`: Raw requisition requirement string.
  - `target_sku`: Correct matching candidate SKU from `inventory_catalog.csv`.
  - `expected_tier`: Expected compatibility tier (`TIER_1_EXACT`, `TIER_2_SUPERSET`, `TIER_3_FUNCTIONAL_EQUIVALENT`, `TIER_4_INCOMPATIBLE`).
  - `expected_violations`: Specific engineering violation codes if Tier 4 (e.g. `["MATING_RF_TO_FF_CAST_IRON_PROHIBITED"]`).
  - `engineering_rationale`: Mechanical and metallurgical justification for evaluation.

### `ocr_payloads.json` — Scanned MTC Document OCR Test Payloads
- **Purpose:** Pre-computed tokenized OCR bounding boxes and extracted text streams from real and synthetic EN 10204 Type 3.1 Material Test Certificates.
- **Contents:**
  - Ladle / Spectral analysis percentages: $\% \text{C}, \% \text{Mn}, \% \text{P}, \% \text{S}, \% \text{Si}, \% \text{Cr}, \% \text{Mo}, \% \text{Ni}$.
  - Mechanical properties: Yield Strength (MPa), Tensile Strength (MPa), Elongation ($\%$), Hardness (HBW/HRC).
  - Heat numbers, mill manufacturer, and testing inspector stamps.

---

## 2. Data Integrity & Usage

```bash
# Verify catalog row count and schema
python -c "import pandas as pd; df = pd.read_csv('data/inventory_catalog.csv'); print(df.info())"
```
