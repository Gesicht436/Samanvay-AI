# Machine Learning Core Workflow: Industrial NER & Semantic Vector Retrieval

**Role:** Machine Learning Lead (Hariom)

**Primary Directory:** `backend/app/ml/`

**Target Environment:** Python 3.14 PyTorch, Hugging Face Transformers, Sentence-Transformers, Qdrant Client


---

### Objective & Architectural Role

Your mission is to build the machine learning intelligence layer for **Samanvay-AI (BharatCodex)**.

Raw, unstructured procurement descriptions across CPSEs (IOCL, ONGC, BPCL) are notoriously abbreviated and inconsistent (e.g., `FLG WNRF 4IN 300# A105` vs. `FLANGE WELD NECK 4" CL300 ASTM A105`). You own the two-step ML pipeline:

1. **Slot-Filling NER:** Parse and isolate hard physical engineering attributes (Size, Rating, Metallurgy, Standards) from raw text strings.
2. **Dense Vector Retrieval:** Map heterogeneous, abbreviated descriptions into a shared semantic vector space using a Bi-Encoder and index them in Qdrant for $<15\text{ ms}$ candidate discovery.

```
Raw Material Text (e.g., "FLG WNRF 4IN 300# A105 ASME B16.5")
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
[Task 1: DeBERTa NER Tagger]         [Task 2: BGE-M3 Bi-Encoder]
       │                                       │
       ▼                                       ▼
Normalized Attribute Schema         Dense Vector Embedding (1024-d)
{                                              │
  "item_type": "FLANGE_WELD_NECK",             ▼
  "size_nb_mm": 100.0,              [Task 3: Qdrant Vector Search]
  "pressure_class": 300,                       │
  "metallurgy": "ASTM_A105",                   ▼
  ...                               Top-10 Candidates Pool 
}                                   (Cosine Similarity >= 0.70)
       │                                       │
       └───────────────────┬───────────────────┘
                           ▼
             Passed downstream to Harsh 
      (ASME Deterministic Validation & Neo4j)
```

---

### Step-by-Step Implementation Guide & Next Actions

#### Step 1: Execute NER Fine-Tuning (`backend/app/ml/train_ner.py`)
* **Input Dataset:** [`data/ml_training/ner_train.jsonl`](file:///D:/Development/Hackathons/Samanvay-AI/data/ml_training/ner_train.jsonl)
* **Base Checkpoint:** `microsoft/deberta-v3-small` (or `roberta-base`).
* **Entities:**
  * `ITEM_TYPE` (e.g., `FLG`, `GATE VALVE`, `BLT`)
  * `SIZE` (e.g., `4IN`, `DN100`, `4"`, `100MM`)
  * `PRESSURE_RATING` (e.g., `300#`, `CLASS 300`, `PN50`, `CL300`)
  * `METALLURGY` (e.g., `A105`, `SS316`, `ASTM A350 LF2`, `WCB`)
  * `FACING_END` (e.g., `WNRF`, `RTJ`, `BW`, `SW`, `FF`)
  * `STANDARD` (e.g., `ASME B16.5`, `API 6D`, `API 600`, `ASTM A193`)
* **Execution:** Train for 3 epochs using Hugging Face `Trainer` with character offset mapping (`return_offsets_mapping=True`). Save final model weights to `backend/app/ml/model_weights/ner_deberta/`.

#### Step 2: Build NER Inference & Normalization Pipeline (`backend/app/ml/ner_tagger.py`)
* **Function:** `extract_attributes(raw_description: str) -> ExtractedMaterialAttributes`
* **Regex & Unit Normalization Rules:**
  * **Dimension Standardizer:** Convert imperial inches (`4"`, `4IN`, `4 INCH`) or DN codes (`DN100`) to metric millimeters float (`100.0`).
  * **Pressure Standardizer:** Strip `#`, `LB`, `CLASS`, or `PN` (`300#`, `300LB`, `CL300` $\rightarrow$ `300`).
  * **Taxonomy Mapper:** Map abbreviations to canonical enums (`FLG` + `WN` $\rightarrow$ `FLANGE_WELD_NECK`, `A105` $\rightarrow$ `ASTM_A105`).
* **Contract Output:** Returns a validated Pydantic model instance (`ExtractedMaterialAttributes`).

#### Step 3: Execute Bi-Encoder Fine-Tuning (`backend/app/ml/train_biencoder.py`)
* **Input Dataset:** [`data/ml_training/biencoder_pairs.jsonl`](file:///D:/Development/Hackathons/Samanvay-AI/data/ml_training/biencoder_pairs.jsonl) (8,000 anchor-positive pairs).
* **Base Model:** `BAAI/bge-m3`.
* **Loss Objective:** `MultipleNegativesRankingLoss(model)`.
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

#### Step 4: Seed Qdrant & Build Search Engine (`backend/app/ml/vector_search.py`)
* **Input Dataset:** [`data/taxonomies/canonical_master.csv`](file:///D:/Development/Hackathons/Samanvay-AI/data/taxonomies/canonical_master.csv) (2,200 canonical materials).
* **Qdrant Setup:** Connect to Qdrant instance (`localhost:6333`). Create collection `canonical_materials` with vector size `1024` and `Distance.COSINE`.
* **Indexing:** Embed all 2,200 canonical descriptions and upload them with full metadata payload (`canonical_id`, `item_type`, `size_nb_mm`, `pressure_class`, `metallurgy`, `unspsc_code`, `gem_category_id`).
* **Query Function:** `get_candidate_skus(raw_description: str, top_k: int = 10) -> list[CandidateMatch]` returning items with cosine score $\ge 0.70$.

---

### File Deliverables & Interface Contracts

Work strictly inside `backend/app/ml/`:

```
backend/app/ml/
├── ner_tagger.py         # Tag extraction + regex normalization logic
├── vector_search.py      # Embedding generation + Qdrant client & indexing
├── train_ner.py          # DeBERTa-v3 token classification training script
├── train_biencoder.py    # BGE-M3 contrastive fine-tuning script
└── model_weights/        # Directory for saved safetensors / checkpoints
```

**Interface Signatures:**

```python
# ner_tagger.py
def extract_attributes(raw_description: str) -> ExtractedMaterialAttributes:
    """Runs token classification + regex normalization to output a validated schema."""
    ...

# vector_search.py
def get_candidate_skus(raw_description: str, top_k: int = 10) -> list[CandidateMatch]:
    """Generates embedding for raw text and queries Qdrant for top-k candidates."""
    ...
```

---

### Status Update: Upstream Data Is Ready!

> [!IMPORTANT]
> **Mock Datasets & Training Fixtures are ALREADY GENERATED and available right now:**
> * **NER Training Data:** [`data/ml_training/ner_train.jsonl`](file:///D:/Development/Hackathons/Samanvay-AI/data/ml_training/ner_train.jsonl) (5,000 annotated records with validated character-level start/end offsets across 6 entity tags).
> * **Bi-Encoder Pairs:** [`data/ml_training/biencoder_pairs.jsonl`](file:///D:/Development/Hackathons/Samanvay-AI/data/ml_training/biencoder_pairs.jsonl) (8,000 anchor-positive contrastive pairs formatted for `MultipleNegativesRankingLoss`).
> * **Canonical Master Catalog:** [`data/taxonomies/canonical_master.csv`](file:///D:/Development/Hackathons/Samanvay-AI/data/taxonomies/canonical_master.csv) (2,200 canonical engineering items ready for Qdrant index seeding).
> * **CPSE Test Catalogs:** [`data/mock_cpes_catalogs/`](file:///D:/Development/Hackathons/Samanvay-AI/data/mock_cpes_catalogs/) (10,800 realistic items across IOCL, ONGC, and BPCL for end-to-end evaluation).
>
> **You are no longer blocked on data. You can start training and building models immediately.**

---

### Downstream Integration Handoff
Once your `extract_attributes` and `get_candidate_skus` functions are callable:
1. **Harsh (`backend/app/matching/tolerance.py`)** receives the extracted attributes and top-10 candidate pool to run zero-tolerance ASME mechanical validation.
2. **Mayank (`backend/app/api/v1/match.py`)** connects your search engine directly to the REST API endpoint for real-time frontend deduplication.
