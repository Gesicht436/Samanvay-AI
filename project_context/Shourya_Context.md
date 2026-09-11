# Data Engineering & Taxonomy Operations Workflow

**Role:** Data Pipelines & Ontology Curation Lead (Shaurya)

**Primary Directory:** `data/` and `backend/app/ingestion/data_pipeline/`

**Target Environment:** Python 3.11 / 3.12, Pandas, Polars, OpenPyXL, JSON/CSV tools

---

### Phase 1 Status: Data Generation & Curation Completed!

> [!NOTE]
> **Phase 1 datasets and generator scripts have been generated and validated:**
> * [`data/curate_taxonomies.py`](file:///D:/Development/Hackathons/Samanvay-AI/data/curate_taxonomies.py) $\rightarrow$ Generated:
>   * [`data/taxonomies/unspsc_v26.csv`](file:///D:/Development/Hackathons/Samanvay-AI/data/taxonomies/unspsc_v26.csv) (20 rows, hierarchical segments, families, classes & commodities)
>   * [`data/taxonomies/gem_categories.csv`](file:///D:/Development/Hackathons/Samanvay-AI/data/taxonomies/gem_categories.csv) (13 rows, GeM public procurement categories)
>   * [`data/taxonomies/canonical_master.csv`](file:///D:/Development/Hackathons/Samanvay-AI/data/taxonomies/canonical_master.csv) (2,200 canonical engineering items with ASME/ASTM specifications)
> * [`data/generate_catalogs.py`](file:///D:/Development/Hackathons/Samanvay-AI/data/generate_catalogs.py) $\rightarrow$ Generated:
>   * [`data/mock_cpes_catalogs/iocl_materials.csv`](file:///D:/Development/Hackathons/Samanvay-AI/data/mock_cpes_catalogs/iocl_materials.csv) (3,600 items with truncated vowel-dropped IOCL dialect)
>   * [`data/mock_cpes_catalogs/ongc_materials.csv`](file:///D:/Development/Hackathons/Samanvay-AI/data/mock_cpes_catalogs/ongc_materials.csv) (3,600 items with verbose comma-delimited ONGC dialect)
>   * [`data/mock_cpes_catalogs/bpcl_materials.csv`](file:///D:/Development/Hackathons/Samanvay-AI/data/mock_cpes_catalogs/bpcl_materials.csv) (3,600 items with compact hyphenated BPCL dialect)
> * [`data/build_train_sets.py`](file:///D:/Development/Hackathons/Samanvay-AI/data/build_train_sets.py) $\rightarrow$ Generated:
>   * [`data/ml_training/ner_train.jsonl`](file:///D:/Development/Hackathons/Samanvay-AI/data/ml_training/ner_train.jsonl) (5,000 NER annotated sequences with verified character offsets)
>   * [`data/ml_training/biencoder_pairs.jsonl`](file:///D:/Development/Hackathons/Samanvay-AI/data/ml_training/biencoder_pairs.jsonl) (8,000 anchor-positive contrastive pairs)
> * [`data/seed_documents.py`](file:///D:/Development/Hackathons/Samanvay-AI/data/seed_documents.py) $\rightarrow$ Generated:
>   * 5 sample EN 10204 3.1 Mill Test Certificates (MTCs) and delivery challan PDFs in [`data/raw/`](file:///D:/Development/Hackathons/Samanvay-AI/data/raw/) along with [`sample_mtc_ground_truth.json`](file:///D:/Development/Hackathons/Samanvay-AI/data/raw/sample_mtc_ground_truth.json).

---

### Revised Workflow: Phase 2 Next Steps

Now that the core synthetic datasets are live and unblocking Hariom, Harsh, Smariddih, and Ranvijay, your focus transitions to ingestion infrastructure, evaluation benchmarks, and graph seeding support:

```
[Phase 1 Complete: 10.8k Catalogs, ML Sets, Taxonomies]
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
[Task 1: Ingestion     [Task 2: Golden       [Task 3: Neo4j
 Batch Validator]       Benchmark Suite]      Seeding Script]
 backend/app/ingestion/  data/evaluation/      backend/app/graph/
 data_pipeline/loader.py benchmark_test_cases.json seed_graph.py
```

---

### Task 1: Ingestion Pipeline Batch Validator (`backend/app/ingestion/data_pipeline/loader.py`)

Build the robust ingestion utility that parses incoming CPSE catalog uploads (`.csv` and `.xlsx`), validates schema headers, and prepares them for the downstream ML and matching pipelines:

* **Key Capabilities to Implement:**
  1. **Format Agnostic Reader:** Handle both UTF-8 CSVs and Excel `.xlsx` spreadsheets using `polars` / `pandas` / `openpyxl`.
  2. **Header Normalizer:** Automatically detect and map common ERP column name variations (e.g., `["Material_Desc", "Short_Text", "ITEM_DESCRIPTION"]` $\rightarrow$ `raw_description`; `["Material_No", "SAP_CODE", "ITEM_CODE"]` $\rightarrow$ `local_code`).
  3. **Batch Streaming Generator:** Yield chunks of 50–100 items to avoid memory spikes during large catalog deduplication runs in Mayank's FastAPI router (`POST /api/v1/ingest/upload`).

* **File Location:** `backend/app/ingestion/data_pipeline/loader.py`

---

### Task 2: Golden Benchmark Evaluation Suite (`data/evaluation/benchmark_test_cases.json`)

To prove to the hackathon judges that Samanvay-AI outperforms generic LLMs and vector search, create a curated golden evaluation suite of **150–200 high-difficulty edge cases**:

* **Evaluation Buckets to Construct:**
  1. **Tier-1 Exact Duplicates (50 pairs):** Different syntax across IOCL, ONGC, and BPCL that represent the exact same engineering item (e.g., `FLG WNRF 4IN 300# A105` vs `FLANGE, WELDING NECK, 4 INCH, CLASS 300, ASTM A105, ASME B16.5, RF`).
  2. **Tier-2 Valid Substitutes (50 pairs):** Higher specification upgrades with matching mating dimensions (e.g., Class 600 substituting Class 300; SS316 flange substituting CS A105 flange in standard temperature duty).
  3. **Tier-3 Hard Incompatibles (50 pairs):** Subtle safety traps that vector embeddings typically miss (e.g., Class 150 trying to substitute Class 300; 50mm size mated with 65mm flange; RTJ facing paired with Raised Face).
  4. **Acronym False-Friends (25 pairs):** Items with overlapping token strings but fundamentally different mechanical functions (e.g., `GATE VALVE` vs `GLOBE VALVE` vs `BALL VALVE`).

* **File Deliverable:** `data/evaluation/benchmark_test_cases.json` containing:
  ```json
  [
    {
      "source_text": "IOCL: FLG WNRF 4IN 150# A105",
      "target_text": "ONGC: FLANGE, WELDING NECK, 4 INCH, CLASS 300, ASTM A105, RF",
      "expected_tier": "TIER_2_SUBSTITUTE",
      "rationale": "Class 300 up-rating permitted with identical facing and metallurgy."
    }
  ]
  ```

---

### Task 3: Neo4j Taxonomy Seeding Script (`backend/app/graph/seed_graph.py`)

Assist Harsh by building the automated Cypher loader script that loads your curated taxonomy tables into Neo4j:

* **Data Sources:**
  * [`data/taxonomies/unspsc_v26.csv`](file:///D:/Development/Hackathons/Samanvay-AI/data/taxonomies/unspsc_v26.csv)
  * [`data/taxonomies/gem_categories.csv`](file:///D:/Development/Hackathons/Samanvay-AI/data/taxonomies/gem_categories.csv)
  * [`data/taxonomies/canonical_master.csv`](file:///D:/Development/Hackathons/Samanvay-AI/data/taxonomies/canonical_master.csv)
* **Graph Operations:**
  * Create unique constraints on `(:CanonicalMaterial {canonical_id})`, `(:UNSPSC_Commodity {code})`, and `(:GeM_Category {category_id})`.
  * Load taxonomy nodes and establish relationships:
    ```cypher
    (:CanonicalMaterial)-[:CLASSIFIED_UNDER]->(:UNSPSC_Commodity)
    (:CanonicalMaterial)-[:LISTED_ON_GEM]->(:GeM_Category)
    ```

---

### Task 4: Extended Mechanical Catalog Expansion (Optional / Stretch)

If time permits, expand the combinatorial matrix to include additional high-volume hydrocarbon refinery equipment:
* **Seamless Line Pipes (API 5L Gr. B / X52 / X65):** Schedules 40, 80, 160, XXS.
* **Buttweld Pipe Fittings (ASME B16.9):** 90-degree elbows, equal tees, concentric reducers (ASTM A234 WPB).
* **Industrial Strainers:** Y-type and Basket strainers (ASTM A216 WCB).

---

### Summary of Repository Responsibilities

```
data/
├── curate_taxonomies.py           # [COMPLETED] Taxonomy tables generator
├── generate_catalogs.py           # [COMPLETED] CPSE catalogs generator
├── build_train_sets.py            # [COMPLETED] NER and Bi-Encoder training sets generator
├── seed_documents.py              # [COMPLETED] Sample MTC PDFs generator
│
├── taxonomies/                    # [READY] UNSPSC, GeM, and Canonical master CSVs
├── mock_cpes_catalogs/            # [READY] IOCL, ONGC, and BPCL catalog CSVs
├── ml_training/                   # [READY] ner_train.jsonl & biencoder_pairs.jsonl
├── raw/                           # [READY] Sample MTC PDFs & challans
└── evaluation/                    # [NEW - Task 2] Benchmark test suite
    └── benchmark_test_cases.json

backend/app/
├── ingestion/data_pipeline/       # [NEW - Task 1]
│   └── loader.py                  # Batch file intake & header normalizer
└── graph/
    └── seed_graph.py              # [NEW - Task 3] Neo4j CSV loader script
```