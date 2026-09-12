# Data Engineering, Semantic Matching & Tier System Workflow

**Role:** Data Pipelines & Semantic Matching Lead + Floating Technical Support (Shourya)

**Collaborators:**
* **Hariom** (You own BGE-M3 bi-encoder fine-tuning & pair with Hariom on ML search)
* **Mayank** (You collaborate on Qdrant Vector DB and assist Mayank on the Tier Distribution System)
* **All Teammates** (Floating support to assist with data, testing, and integration)

**Primary Directories:** `data/`, `backend/app/ml/`, `backend/app/matching/`, `backend/app/ingestion/data_pipeline/`

**Target Environment:** Python 3.14, Sentence-Transformers, Qdrant Client, Pandas, Polars, OpenPyXL, JSON/CSV

---

### Objective & Architectural Role

You are the versatile data and matching specialist for **Samanvay-AI (BharatCodex)**. Having already generated the core synthetic catalogs, ML training pairs, and taxonomy CSVs in Phase 1, you now take on high-impact responsibilities across semantic matching, vector search, and safety rules:

1. **Semantic Matching Engine:** Fine-tune the `BAAI/bge-m3` Bi-Encoder on 8,000 contrastive pairs to project messy procurement descriptions into dense 1024-d vectors (helping Hariom).
2. **Qdrant Vector Database Collaboration:** Partner with Mayank to set up Qdrant, seed the 2,200 canonical materials, and expose sub-15ms candidate retrieval (`vector_search.py`).
3. **Tier Distribution System Assistance:** Partner with Mayank to build and validate the deterministic ASME B16.5 / ASTM tolerance rule engine (`backend/app/matching/tolerance.py`).
4. **Ingestion Batch Loader:** Build the streaming CSV/Excel reader that powers Mayank's upload endpoint.
5. **Golden Benchmark Evaluation Suite:** Curate 150–200 edge cases proving system accuracy over generic LLMs.
6. **Floating Support:** Troubleshoot and unblock teammates wherever needed across the stack.

```
Incoming Catalog Upload / Query Text
                 │
  ┌──────────────┴──────────────┐
  ▼                             ▼
[Task 1: Batch Loader]    [Task 2: BGE-M3 Bi-Encoder]
(`app/ingestion/loader.py`) (`app/ml/train_biencoder.py`)
  • Stream 10k items            • Fine-tuned on 8k pairs
  • Normalize headers           • 1024-d Dense Embedding
                                │
                                ▼
                   [Task 3: Qdrant Vector Search]
                   (Collaborating with Mayank)
                    • Canonical Master Index (2,200 SKUs)
                    • Sub-15ms Top-10 Candidate Pool
                                │
                                ▼
                 [Task 4: Tier Distribution System]
                     (Assisting Mayank on Rules)
                    • ASME B16.5 & ASTM Tolerance Checks
                    • Tier-1 (Exact), Tier-2 (Upgrade), Tier-3 (Reject)
                                │
                                ▼
                 [Task 5: Golden Benchmark Suite]
                 (`data/evaluation/benchmark_test_cases.json`)
```

---

### Step-by-Step Implementation Guide

#### Task 1: Semantic Matching Bi-Encoder Fine-Tuning (`backend/app/ml/train_biencoder.py`)
* **Input Dataset:** [`data/ml_training/biencoder_pairs.jsonl`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/ml_training/biencoder_pairs.jsonl) (8,000 anchor-positive pairs).
* **Base Model:** `BAAI/bge-m3`.
* **Objective:** `MultipleNegativesRankingLoss(model)`.
* **Execution:**
  ```python
  from sentence_transformers import SentenceTransformer, InputExample, losses
  from torch.utils.data import DataLoader
  import json

  train_examples = []
  with open("data/ml_training/biencoder_pairs.jsonl", "r", encoding="utf-8") as f:
      for line in f:
          data = json.loads(line)
          train_examples.append(InputExample(texts=[data["anchor"], data["positive"]]))

  model = SentenceTransformer("BAAI/bge-m3")
  train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=32)
  train_loss = losses.MultipleNegativesRankingLoss(model)

  model.fit(
      train_objectives=[(train_dataloader, train_loss)],
      epochs=3,
      warmup_steps=100,
      show_progress_bar=True
  )
  model.save("backend/app/ml/model_weights/bge_m3_cpes/")
  ```

#### Task 2: Qdrant Vector Index Collaboration (with Mayank) (`backend/app/ml/vector_search.py`)
* Connect to Qdrant instance (`localhost:6333`).
* Collection: `canonical_materials`, vector size `1024`, `Distance.COSINE`.
* Seed all 2,200 canonical items from [`data/taxonomies/canonical_master.csv`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/taxonomies/canonical_master.csv) with full payload metadata.
* Function: `get_candidate_skus(raw_description: str, top_k: int = 10) -> list[CandidateMatch]` returning candidates with cosine score $\ge 0.70$ in $<15\text{ ms}$.

#### Task 3: Tier Distribution System Assistance (with Mayank) (`backend/app/matching/`)
* Assist Mayank in writing and verifying the pure-Python deterministic tolerance matrix in `tolerance.py` and `asme_rules.py`:
  * Zero tolerance on size (`candidate.size != source.size` $\rightarrow$ Tier-3).
  * Pressure rating compatibility (down-rating strictly forbidden; up-rating permitted if facing/bolts match).
  * ASTM alloy compatibility graph (CS A105 $\rightarrow$ SS316 permitted upgrade; SS316 $\rightarrow$ A105 forbidden downgrade).
  * Tier output: `TIER_1_IDENTICAL`, `TIER_2_SUBSTITUTE`, `TIER_3_INCOMPATIBLE`.

#### Task 4: Ingestion Batch Validator (`backend/app/ingestion/data_pipeline/loader.py`)
* Handle both UTF-8 CSVs and Excel `.xlsx` spreadsheets using `polars` / `pandas` / `openpyxl`.
* Header Normalizer: Map messy ERP headers (`["Material_Desc", "Short_Text", "ITEM_DESCRIPTION"]` $\rightarrow$ `raw_description`).
* Batch Streaming Generator: Stream chunks of 50–100 items to keep memory flat.

#### Task 5: Golden Benchmark Evaluation Suite (`data/evaluation/benchmark_test_cases.json`)
* Create a curated test suite of 150–200 edge cases:
  * 50 Tier-1 Exact Duplicates (cross-dialect).
  * 50 Tier-2 Valid Upgrades (higher specification, matching mating interfaces).
  * 50 Tier-3 Safety Incompatibles (subtle pressure/size/alloy safety traps).
  * 25 Acronym False-Friends (e.g., Gate vs Globe vs Ball Valve).

---

### File Deliverables & Directory Layout

```
backend/app/ml/
├── train_biencoder.py                 # BGE-M3 contrastive fine-tuning script
└── vector_search.py                   # Qdrant client & search logic (with Mayank)

backend/app/matching/
├── asme_rules.py                      # ASME & ASTM tolerance matrices (assisting Mayank)
└── tolerance.py                       # Tier distribution logic (assisting Mayank)

backend/app/ingestion/data_pipeline/
└── loader.py                          # Batch catalog parser & header normalizer

data/evaluation/
└── benchmark_test_cases.json          # 150-case golden evaluation benchmark
```

---

### Team Collaboration & Handoffs
1. **With Hariom:** You own semantic vector matching while Hariom owns NER attribute extraction and feature engineering.
2. **With Mayank:** You collaborate on the Qdrant vector database and assist on the Tier Distribution System rules.
3. **With Harsh:** Your curated taxonomy CSVs in `data/taxonomies/` feed Harsh's Neo4j `seed_graph.py` script.
4. **To the Whole Team:** You provide floating support and run the benchmark suite to prove system accuracy.