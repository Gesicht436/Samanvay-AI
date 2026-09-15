# Datasets, Catalogs & Evaluation Benchmarks (`data`)

## 1. Overview
The `data` directory contains all reference taxonomies, simulated CPSE enterprise catalogs, real scanned procurement documents, and automated evaluation benchmark suites.

---

## 2. Directory Structure

```
data/
|-- evaluation/                  # 150-Case Golden Benchmark evaluation suite
|   |-- benchmark_test_cases.json# Curated test cases (Tier 1, Tier 2, Tier 3)
|   |-- build_benchmark.py       # Generator script for the benchmark suite
|   |-- run_benchmark.py         # Automated benchmark execution engine
|   `-- README.md                # Golden Benchmark detailed methodology
|-- mock_cpes_catalogs/          # Generated ERP catalogs for IOCL, ONGC, and BPCL
|   |-- bpcl_kochi_catalog.csv   # BPCL inventory with SAP naming conventions
|   |-- iocl_panipat_catalog.csv # IOCL inventory with legacy MM conventions
|   `-- ongc_hazira_catalog.csv  # ONGC inventory with Maximo conventions
|-- scanned_images/              # 7 real procurement MTC & inspection documents
|   |-- Image (1).jpeg           # EN 10204 3.1 MTC (MAG General Business - Flanges)
|   |-- Image (2).jpeg           # EN 10204 3.1.B Abnahmepruefzeugnis (Erne Fittings)
|   |-- Image (3).jpeg           # EN 10204 3.1 MTC (R.N. Gupta & Co - RTJ Flanges)
|   |-- Image (4).jpeg           # EN 10204 3.1 Delivery Challan (C&N Industrial)
|   |-- Image (5).jpeg           # Actuator Technical Data Sheet (APV Torqturn)
|   |-- Image (6).jpeg           # EN 10204 3.1 MTC (Phedora - Super Duplex S32750)
|   `-- Image (7).jpeg           # EN 10204 2.2 MTC (Flowsource - 316L Sanitary)
|-- taxonomies/                  # Master cross-walks for UNSPSC and GeM
|   |-- gem_categories.json      # Government e-Marketplace procurement codes
|   `-- unspsc_v26.json          # UNSPSC v26 Commodity Class hierarchy
|-- build_train_sets.py          # Script generating training triplets for bi-encoders
|-- curate_taxonomies.py         # Script establishing taxonomic linkages
|-- generate_catalogs.py         # Generator for 2,200 canonical & 10,800 depot SKUs
|-- seed_documents.py            # Prepares sample invoices and test files
`-- README.md                    # This file
```

---

## 3. Real Scanned Documents (`data/scanned_images`)
The system includes 7 real-world procurement documents used to validate the OCR and MTC extraction pipeline:
- `Image (1).jpeg`: Multi-item MTC containing 12 flange items across Class 150, 300, and 600.
- `Image (2).jpeg`: German-English MTC listing 9 weld neck flanges from 1" to 16" NB.
- `Image (3).jpeg`: High-pressure RTJ blind flange certificate from an Indian forging manufacturer.
- `Image (4).jpeg`: Delivery challan for 4 weld neck flanges with heat numbers.
- `Image (5).jpeg`: Pneumatic valve actuator technical data sheet with torque and enclosure specs.
- `Image (6).jpeg`: Super Duplex Stainless Steel (ASTM A815 S32750) buttweld elbow test certificate.
- `Image (7).jpeg`: Stainless Steel 316L sanitary BPE ferrule certificate.

---

## 4. Catalog Generation Utility (`generate_catalogs.py`)
To regenerate the 2,200 Canonical Master Items and 10,800 simulated CPSE inventory records:
```powershell
uv run python data/generate_catalogs.py
```
This script creates consistent physical parameters across the mock catalogs while applying the authentic naming dialect of each enterprise (e.g. `CL300` for ONGC, `300#` for IOCL, `PN50` for BPCL).
