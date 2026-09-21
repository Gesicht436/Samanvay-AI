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
   - **data.gov.in (MoPNG / PPAC):** Ministry of Petroleum and Natural Gas refinery infrastructure throughput and CPSE operational facility profiles.
   - **Central Public Procurement Portal (CPPP - `eprocure.gov.in`):** Public tender documents and equipment technical indents from IOCL, ONGC, BPCL, HPCL, and GAIL.
   - **Government e-Marketplace (GeM - `gem.gov.in`):** Public industrial product categories (`GeM/CAT/VALVES/...`, `GeM/CAT/PIPES/...`, `GeM/CAT/FLANGES/...`).
   - **Indian GST HSN Classification:** Official Harmonized System of Nomenclature tariff codes:
     - `8481`: Industrial Valves (Gate, Globe, Check, Ball, Butterfly, PSV)
     - `7304`: Seamless Iron and Steel Tubes & Line Pipes
     - `7307`: Pipe Fittings & ASME Flanges
     - `7318`: Stud Bolts and Heavy Hex Nuts
     - `8484`: Spiral Wound & Metallic Ring Joint Gaskets
     - `8413`: Centrifugal Pump Spares (Impellers, Sleeves, Mechanical Seals)

2. **Strict Metallurgy & Physical Compatibility Matrix:**
   Unlike unconstrained random mock data, every catalog row enforces real-world ASME / ASTM / API physical pairings:
   - **Flanges (ASME B16.5):** ASTM A105, A350 LF2, A182 F304L, A182 F316L, A182 F51 Duplex, A182 F53 Super Duplex, A182 F11, A182 F22, Inconel 625.
   - **Valves (API 600 / 602 / 609 / 6D / ASME B16.34):** Cast bodies ASTM A216 WCB, A352 LCB, A351 CF8M; Forged bodies ASTM A105, A350 LF2, A182 F316L; API 600 Trims 1 (13Cr), 5 (Stellite), 8 (13Cr/Stellite), 12 (316/Stellite), 16 (Full 316L).
   - **Line Pipes (ASME B36.10M / API 5L PSL2):** ASTM A106 Gr. B, ASTM A333 Gr. 6, API 5L Gr. B / X52 / X60 / X65, ASTM A312 TP304L / TP316L.
   - **Buttweld Fittings (ASME B16.9):** ASTM A234 WPB, ASTM A420 WPL6, ASTM A403 WP304L / WP316L.
   - **Fasteners (ASME B18.2.1 / B18.2.2):** Matched pairs: ASTM A193 B7 + A194 2H, ASTM A193 B16 + A194 7, ASTM A320 L7 + A194 7, ASTM A193 B7M + A194 2HM (NACE MR0175 sour service), ASTM A193 B8M + A194 8M.
   - **Gaskets (ASME B16.20):** Spiral Wound SS316L/Grafoil with solid inner ring, Octagonal RTJ Soft Iron / SS316.

3. **Multi-CPSE Facility Allocations (5,000 Records):**
   - **IOCL (30% - 1,500 records):** Panipat, Mathura, Koyali, Paradip, Barauni, Guwahati, Digboi, Haldia, Bongaigaon.
   - **ONGC (30% - 1,500 records):** Hazira Gas Complex, Uran Complex, Ankleshwar Asset, Mumbai High Offshore Base, Rajahmundry, Mehsana, Karaikal.
   - **BPCL (15% - 750 records):** Mumbai Mahul Refinery, Kochi Refinery, Bina Refinery.
   - **HPCL (15% - 750 records):** Mumbai Refinery, Visakh Refinery, Bathinda Refinery (HMEL JV).
   - **GAIL (10% - 500 records):** Pata Petrochemicals, Vijaipur Gas Complex, Vaghodia Compressor Station, Usar LPG Plant.

---

## 3. Schema Reference: `inventory_catalog.csv`

| Column | Type | Example | Description |
|---|---|---|---|
| `sku_code` | String | `IOCL-FLG-00001` | Enterprise SKU identifier |
| `cpse_name` | String | `IOCL` | Public sector enterprise (`IOCL`, `ONGC`, `BPCL`, `HPCL`, `GAIL`) |
| `depot_location` | String | `Panipat Refinery, Haryana` | Authentic plant or logistics supply base |
| `raw_description` | String | `FLG WNRF 4IN 300# ASTM A105` | Uncurated ERP description in enterprise dialect |
| `quantity` | Integer | `85` | Physical stock count on hand |
| `unit_cost_inr` | Float | `6480.50` | Book value in INR based on metallurgy tiers |
| `days_idle` | Integer | `420` | Operating age (`<90` active, `91-365` potential surplus, `>365` declared surplus) |
| `po_no` | String | `IOCL/PO/2024/198246` | CPSE purchase order reference |
| `heat_no` | String | `HT-B40495` | Steel mill ladle test heat identifier |
| `standard` | String | `ASME B16.5` | Manufacturing & dimensional engineering standard |
| `hsn_code` | String | `73072100` | Indian Customs / GST 8-digit HSN code |
| `gem_category` | String | `GeM/CAT/FLANGES/ASME/B16.5` | Government e-Marketplace category |
| `mesc_code` | String | `74.20.15.150.1` | MESC industrial classification code |
| `cppp_tender_id` | String | `CPPP/2025/IOCL_688508` | Central Public Procurement Portal tender ID |

---

## 4. Regenerating the Dataset

To re-run the procedural generator:

```bash
uv run python datasets/generators/generate_datasets.py
```
