# Datasets & Training Corpora (`datasets/`)

This directory maintains the primary, canonical datasets, benchmarks, and OCR test payloads powering **Samanvay-AI**'s cross-enterprise material matching pipeline.

> [!NOTE]
> The legacy duplicate `data/` directory has been removed. All configuration, seeders, test suites, and models now exclusively reference `datasets/`.

---

## 1. Directory Structure

```
datasets/
├── inventory_catalog.csv     # 5,000 authentic rows multi-CPSE master catalog
├── golden_benchmarks.json    # 150 expert-annotated matching benchmark pairs (21 safety rules)
├── ocr_payloads.json         # 500 Material Test Certificate OCR payloads
└── generators/               # Deterministic, physically grounded dataset generators
    ├── generate_datasets.py  # Procedural CPSE dialect, tender, and catalog generator
    └── README.md             # Generator documentation and distribution parameters
```

---

## 2. Grounded Data Sources & Engineering Integrity

Internal line-item warehouse stock balances are operational assets proprietary to each enterprise (the foundational rationale for SIH 26099: Inter-CPSE Inventory Silos). However, technical equipment specifications, procurement indents, and tender awards are strictly governed by Indian public sector standards:

1. **Government of India Portals & Registries:**
   - **Central Public Procurement Portal (CPPP - `eprocure.gov.in`):** Public tender documents, equipment technical indents, and tender references from OIL, NRL, IOCL, ONGC, BPCL, HPCL, and GAIL.
   - **Government e-Marketplace (GeM - `gem.gov.in`):** Official industrial product categories (`GeM/CAT/FLANGES/...`, `GeM/CAT/VALVES/...`, `GeM/CAT/PIPES/...`).
   - **Public Procurement (Preference to Make in India) Order (DPIIT):** Class-I local suppliers ($\ge 50\%$ local content), Class-II local suppliers ($20\% - 50\%$), and Non-Local suppliers ($< 20\%$).
   - **Indian GST HSN Classification:** Official Harmonized System of Nomenclature tariff codes (`8481` Valves, `7304` Line Pipes, `7307` Flanges & Fittings, `7318` Fasteners, `8484` Gaskets, `8413` Pumps).

2. **Indian National & Oil Industry Technical Standards:**
   - **Bureau of Indian Standards (BIS):** `IS 2062 Grade E250` (Structural Carbon Steel), `IS 14846 FG 200` (Sluice/Gate Valves), `IS 1239 Part 1 Heavy` (Mild Steel Tubes/Pipes), `IS 1367 Part 3 Class 8.8` (Threaded Fasteners), `IS 9890` (Ball Valves).
   - **Oil Industry Standards:** `EIL Standard Specifications 6-44-0005` (Piping Material), `EIL 6-44-0012` (Valves), `OISD-RP-126` (Refinery Valve Selection & Operation), `OISD-STD-118` (Pipeline Safety Layouts).
   - **OIL Material Codes (MESC):** Standardized 10-digit dot-delimited MESC classifications (e.g. `04.01.24.18.02` for Weld Neck Flanges, `02.10.15.82.11` for Gate Valves).
   - **Dual Engineering Units:** Metric Primary with Imperial Parenthetical notation (e.g. `100 mm NB (4 IN)`, `50 Bar (PN 50) / Class 300#`).

3. **Multi-CPSE Facility Allocations (5,000 Records):**
   - **Oil India Limited (OIL - 30%, 1,500 records):** Central Materials Warehouse Duliajan (Assam), Moran Supply Base (Charaideo), Guwahati Pipeline HQ, Jodhpur Heavy Oil Base (Rajasthan), Kakinada KG Offshore Depot (AP).
   - **Numaligarh Refinery Limited (NRL - 10%, 500 records):** Numaligarh Refinery Yard (Golaghat, Assam).
   - **IOCL (20%, 1,000 records):** Panipat, Mathura, Koyali, Paradip, Barauni, Digboi, Bongaigaon.
   - **ONGC (16%, 800 records):** Assam Asset Base (Nazira), Hazira Gas Complex, Uran Complex, Mumbai High Offshore Base.
   - **BPCL (10%, 500 records):** Mumbai Mahul Refinery, Kochi Refinery, Bina Refinery.
   - **HPCL (8%, 400 records):** Mumbai Refinery, Visakh Refinery.
   - **GAIL (6%, 300 records):** Pata Petrochemicals, Vijaipur Gas Complex.

---

## 3. Schema Reference: `inventory_catalog.csv`

| Column | Type | Example | Description |
|---|---|---|---|
| `sku_code` | String | `OIL-FLG-00142` | Unique enterprise SKU identifier |
| `oil_material_code` | String | `04.01.24.18.02` | Standardized OIL MESC classification code |
| `cpse` | String | `OIL` | Operating CPSE (`OIL`, `NRL`, `IOCL`, `ONGC`, `BPCL`, `HPCL`, `GAIL`) |
| `depot_location` | String | `Central Materials Warehouse, Duliajan` | Physical storage depot or supply base |
| `description` | String | `OIL MESC 04.01.24.18.02 FLG WNRF 100 MM NB (4IN) PN 50 (300#) IS 2062 E250...` | Full engineering catalog description |
| `category` | String | `FLANGE` | Component category (`FLANGE`, `VALVE`, `PIPE`, `FASTENER`, `GASKET`, `ROTATING`) |
| `metallurgy` | String | `IS 2062 Grade E250 / ASTM A105` | Material grade (BIS / ASTM dual spec) |
| `nominal_bore_mm` | String | `100 mm NB` | Metric nominal diameter |
| `pressure_rating_bar` | String | `50 Bar (PN 50)` | Metric pressure rating in Bar / PN |
| `pressure_class` | String | `300#` | Imperial pressure class rating |
| `indian_standard` | String | `IS 2062 Grade E250 / IS 6392` | Bureau of Indian Standards (BIS) reference |
| `oil_std_spec` | String | `EIL 6-44-0005` | Oil Industry (OISD / EIL) engineering specification |
| `gem_category_id` | String | `GeM/CAT/FLANGES/PN50/IS2062` | Government e-Marketplace product category |
| `cppp_tender_ref` | String | `OIL/DUL/MAT/2026/0142` | Central Public Procurement Portal tender reference |
| `make_in_india_class` | String | `Class-I` | DPIIT MII preference category (`Class-I`, `Class-II`, `Non-Local`) |
| `local_content_percentage` | Float | `84.5` | Declared indigenous manufacturing content ($\%$) |
| `quantity` | Integer | `18` | Available physical stock count |
| `unit` | String | `EA` | Unit of measurement (`EA`, `MTR`, `SET`) |
| `unit_cost_inr` | Float | `14250.00` | Commercial inventory book value in INR |
| `days_idle` | Integer | `142` | Days non-moving in warehouse storage |
| `heat_no` | String | `HT-Z64987` | Steel mill ladle test heat identifier |

---

## 4. Regenerating & Reseeding the Dataset

To regenerate the 5,000-item catalog:
```bash
uv run python datasets/generators/generate_datasets.py
```

To reseed the PostgreSQL database and Qdrant vector collection:
```bash
uv run python scripts/seed_database.py --force
```
