# Datasets, Benchmarks & Training Corpora (`datasets/`)

This directory maintains the primary canonical datasets, ground-truth evaluation benchmarks, and optical character recognition payloads powering **Samanvay-AI**'s cross-enterprise material matching and substitution platform.

In public sector oil, gas, and petrochemical operations, live warehouse line-item stock balances are confidential operational assets proprietary to each enterprise (the foundational challenge of inter-CPSE inventory silos). However, technical equipment specifications, procurement indents, and tender awards are strictly governed by Indian public sector procurement frameworks, the Bureau of Indian Standards (BIS), the Oil Industry Safety Directorate (OISD), and Engineers India Limited (EIL).

The datasets in this directory are procedurally generated with mathematical and metallurgical ground truth, reflecting authentic enterprise dialects, realistic 12–15% field sparsity, dual engineering units, and Government of India regulatory classifications.

---

## 1. Directory Structure

```
datasets/
├── inventory_catalog.csv     # Master 5,000-row multi-CPSE industrial inventory catalog
├── golden_benchmarks.json    # 150 expert-verified paired test cases (evaluating 21 safety modules)
├── ocr_payloads.json         # 500 Material Test Certificate OCR payloads (with noise & degradation)
├── README.md                 # Master dataset catalog and schema documentation
└── generators/               # Procedural multi-enterprise dataset generation scripts
    ├── generate_datasets.py  # Deterministic catalog, dialect, and benchmark generator
    └── README.md             # Procedural generator documentation and configuration guide
```

---

## 2. Dataset Overview

### 1. `inventory_catalog.csv` (5,000 Records)
A comprehensive master catalog spanning 7 major public sector hydrocarbon enterprises across 14 equipment categories (Pipes, Flanges, Gate Valves, Globe Valves, Check Valves, Ball Valves, Butterfly Valves, 90° Elbows, Equal Tees, Concentric Reducers, Stud Bolts, Spiral Wound Gaskets, RTJ Gaskets, PSV Valves, and Centrifugal Pump Spares).

- **Multi-CPSE Pan-India Allocations:**
  - **Oil India Limited (OIL - 30%, 1,500 records):** Central Materials Warehouse Duliajan (Assam), Moran Drilling Base (Charaideo), Digboi Support Depot (Tinsukia), Guwahati Pipeline Operations HQ, Jorhat Logistics Base, Jodhpur Heavy Oil Base (Rajasthan), Kakinada KG Offshore Supply Base (AP).
  - **Numaligarh Refinery Limited (NRL - 10%, 500 records):** Numaligarh Refinery Materials Yard (Golaghat, Assam).
  - **Indian Oil Corporation Limited (IOCL - 15%, 750 records):** Panipat, Mathura, Koyali, Paradip, Barauni, Digboi, Haldia, Bongaigaon.
  - **Oil and Natural Gas Corporation (ONGC - 15%, 750 records):** Hazira Gas Complex, Uran Gas Complex, Ankleshwar Asset, Mumbai High Offshore Base, Rajahmundry Asset, Mehsana, Karaikal.
  - **Bharat Petroleum Corporation Limited (BPCL - 10%, 500 records):** Mumbai Mahul Refinery, Kochi Refinery, Bina Refinery.
  - **Hindustan Petroleum Corporation Limited (HPCL - 10%, 500 records):** Mumbai Refinery, Visakh Refinery, Bathinda Refinery (HMEL JV).
  - **Gas Authority of India Limited (GAIL - 10%, 500 records):** Pata Petrochemicals, Vijaipur Gas Complex, Vaghodia Compressor Station, Usar LPG Plant.

### 2. `golden_benchmarks.json` (150 Paired Test Cases)
Expert-verified substitution pairs designed to systematically evaluate matching precision and verify the 21 deterministic safety modules:
- **Tier 1 (50 Cases):** Identical parity and dimension-preserving safe over-ratings ($\ge 95\%$ match score, zero engineering risk).
- **Tier 2 (50 Cases):** Functional substitutions requiring engineering review ($80\% - 94\%$ match score, e.g. higher alloy upgrade, schedule over-thickness, Stellite trim upgrade).
- **Tier 3 (50 Cases):** Hard safety hazard rejections ($< 80\%$ match score, triggering explicit ASME/API violation codes, e.g. pressure class downgrade, non-sour trim in sour service, size mismatch).

### 3. `ocr_payloads.json` (500 MTC Payloads)
Realistic Material Test Certificate extractions simulating PaddleOCR output from EN 10204 3.1/3.2 certificates:
- Includes certificate numbers, heat numbers, purchase order references, approved mill manufacturers (SAIL, Tata, L&T, Jindal), and TPI inspection agencies (EIL, Lloyd's, DNV, TÜV, IRS, BV).
- Chemical ladle analyses ($\% \text{C}, \% \text{Mn}, \% \text{Si}, \% \text{P}, \% \text{S}, \% \text{Cr}, \% \text{Ni}, \% \text{Mo}, \% \text{V}, \% \text{Cu}, \% \text{N}$).
- Mechanical tensile properties (Yield Strength, Tensile Strength, Elongation, Charpy V-Notch impact at $-46^\circ\text{C}$, Brinell hardness).
- Injected with $10\%$ low-confidence OCR tokens and $5\%$ OCR noise/stamp degradation to stress-test parser resilience.

---

## 3. Regulatory Alignment & Indian Public Sector Standards

The datasets strictly reflect the statutory and technical standards governing Indian enterprise procurement:

1. **Public Procurement Portals:**
   - **Central Public Procurement Portal (CPPP - `eprocure.gov.in`):** Standard tender reference formats (e.g. `OIL/DUL/MAT/2026/0142`, `2026_IOCL_458921_1`).
   - **Government e-Marketplace (GeM - `gem.gov.in`):** Category IDs (e.g. `GeM/CAT/FLANGES/ASME/B16.5`, `GeM/CAT/VALVES/GATE/API600`).
   - **Public Procurement (Preference to Make in India) Order (DPIIT):** Class-I local suppliers ($\ge 50\%$ local content), Class-II ($20\% - 50\%$), and Non-Local ($< 20\%$).
   - **Indian GST HSN Classification:** Official Harmonized System of Nomenclature tariff codes (`8481` Valves, `7304` Line Pipes, `7307` Flanges & Fittings, `7318` Fasteners, `8484` Gaskets, `8413` Pumps).

2. **National Technical Standards:**
   - **Bureau of Indian Standards (BIS):** `IS 2062 Grade E250` (Structural Carbon Steel), `IS 14846 FG 200` (Sluice/Gate Valves), `IS 1239 Part 1 Heavy` (Mild Steel Tubes/Pipes), `IS 3589 Fe 410` (Large Diameter Steel Pipes), `IS 1367 Part 3 Class 8.8` (Threaded Fasteners), `IS 9890` (Ball Valves), `IS 13095` (Butterfly Valves), `IS 5312` (Check Valves), `IS 6392` (Flanges).
   - **Oil Industry Standards:** `EIL 6-44-0005` (Piping Material), `EIL 6-44-0012` (Valves), `OISD-RP-126` (Refinery Valve Selection & Operation), `OISD-STD-118` (Pipeline Safety Layouts).
   - **OIL SAP Material Codes (MESC):** Standardized 8-digit dot-delimited MESC classifications (e.g. `04.01.24.18.02` for Weld Neck Flanges, `02.10.15.82.11` for Gate Valves).
   - **Dual Engineering Units:** Metric Primary with Imperial Parenthetical notation (e.g. `100 mm NB (4 IN)`, `50 Bar (PN 50) / Class 300#`).

---

## 4. Schema Reference: `inventory_catalog.csv`

| Column Name | Data Type | Example Value | Description |
|---|---|---|---|
| `sku_code` | String | `OIL-FLG-00142` | Unique enterprise stock-keeping unit identifier |
| `oil_material_code` | String | `04.01.24.18.02` | Standardized OIL 8-digit SAP MESC classification code |
| `cpse` | String | `OIL` | Sovereign operating enterprise (`OIL`, `NRL`, `IOCL`, `ONGC`, `BPCL`, `HPCL`, `GAIL`) |
| `depot_location` | String | `OIL Central Materials Warehouse, Duliajan, Assam` | Physical warehouse facility or supply base |
| `description` | String | `OIL MESC 04.01.24.18.02 FLG WNRF 100 MM NB (4IN) PN 50 (300#) IS 2062 E250 / ASME B16.5 ASTM A105 RF MII Class-I (84.5%)` | Full technical engineering catalog description |
| `category` | String | `FLANGE` | Component category |
| `item_type` | String | `FLANGE` | Normalized mechanical equipment family |
| `metallurgy` | String | `IS 2062 Grade E250 / ASTM A105` | Metallurgical material grade |
| `nominal_bore_mm` | Float | `100.0` | Metric nominal bore diameter in millimeters |
| `size` | String | `4IN` | Imperial or metric nominal size |
| `pressure_class` | String | `300#` | ASME pressure rating class |
| `pressure_rating_bar` | Float | `50.0` | Metric pressure rating in Bar / PN |
| `schedule` | String | `SCH 40` | Pipe schedule or wall thickness designation |
| `facing` | String | `RF` | Flange or valve end facing (`RF`, `RTJ`, `FF`, `BW`, `SW`) |
| `trim` | String | `TR8` | Valve internal trim designation (API trim number or alloy) |
| `quantity` | Integer | `18` | Available physical stock quantity |
| `unit` | String | `EA` | Unit of measurement (`EA`, `MTR`, `SET`) |
| `unit_cost_inr` | Float | `14250.00` | Commercial inventory book value in Indian Rupees |
| `days_idle` | Integer | `142` | Number of days non-moving in storage |
| `heat_no` | String | `HT-Z64987` | Mill test ladle heat identifier |
| `standard` | String | `ASME B16.5` | International manufacturing design standard |
| `indian_standard` | String | `IS 2062 Grade E250 / IS 6392` | Bureau of Indian Standards (BIS) reference |
| `oil_std_spec` | String | `EIL 6-44-0005` | Oil industry engineering specification |
| `gem_category_id` | String | `GeM/CAT/FLANGES/ASME/B16.5` | Government e-Marketplace procurement category |
| `cppp_tender_ref` | String | `OIL/DUL/MAT/2026/0142` | Central Public Procurement Portal tender reference |
| `make_in_india_class` | String | `Class-I` | DPIIT MII preference category (`Class-I`, `Class-II`, `Non-Local`) |
| `local_content_percentage` | Float | `84.5` | Certified domestic local manufacturing content percentage |

---

## 5. Dataset Regeneration & Reseeding

To regenerate the entire dataset suite (5,000-row catalog, 150 golden benchmarks, and 500 OCR payloads):

```bash
# Execute procedural dataset generator
python datasets/generators/generate_datasets.py
```

To reseed the PostgreSQL relational schema, Qdrant vector database collections, and Neo4j property star graph:

```bash
# Force re-seed database cluster from generated datasets
python scripts/seed_database.py --force
```
