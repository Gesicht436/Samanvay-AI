# Machine Learning Core Workflow: Feature Engineering & Industrial NER

**Role:** Machine Learning Lead (Hariom)

**Collaborators:** 
* **Shourya** (Owns BGE-M3 Bi-Encoder fine-tuning & Semantic Matching; assists ML pipeline)
* **Mayank** (Builds Tier Distribution System & collaborates with Shourya on Qdrant Vector DB)

**Primary Directory:** `backend/app/ml/`

**Target Environment:** Python 3.14, PyTorch, Hugging Face Transformers, Pydantic v2

---

### Objective & Architectural Role

Your mission is to build the attribute extraction and feature engineering intelligence layer for **Samanvay-AI (BharatCodex)**.

Raw, unstructured procurement descriptions across CPSEs (IOCL, ONGC, BPCL) are notoriously abbreviated and inconsistent (e.g., `FLG WNRF 4IN 300# A105` vs. `FLANGE WELD NECK 4" CL300 ASTM A105`). 

You own the **Feature Engineering & Slot-Filling NER** pipeline:
1. **Slot-Filling NER:** Train and run token classification models (`DeBERTa-v3`) to isolate hard physical engineering attributes (Item Type, Size, Pressure Rating, Metallurgy, Facing, Standards) from raw text.
2. **Feature Engineering & Normalization:** Build robust deterministic standardizers converting imperial/DN sizes to metric millimeters, stripping pressure symbols into standardized integer classes, and mapping messy alloy codes to canonical identifiers.

```
Raw Material Text (e.g., "FLG WNRF 4IN 300# A105 ASME B16.5")
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
[Hariom: Feature Engineering & NER]     [Shourya: BGE-M3 Bi-Encoder]
       │                                       │
       ▼                                       ▼
Normalized Attribute Schema             Dense Vector Embedding (1024-d)
{                                              │
  "item_type": "FLANGE_WELD_NECK",             ▼
  "size_nb_mm": 100.0,                  [Shourya & Mayank: Qdrant Index]
  "pressure_class": 300,                       │
  "metallurgy": "ASTM_A105",                   ▼
  ...                                   Top-10 Candidates Pool 
}                                       (Cosine Similarity >= 0.70)
       │                                       │
       └───────────────────┬───────────────────┘
                           ▼
              Passed downstream to Mayank & Shourya 
                 (Tier Distribution System)
```

---

### Step-by-Step Implementation Guide

#### Step 1: Execute NER Fine-Tuning (`backend/app/ml/train_ner.py`)
* **Input Dataset:** [`data/ml_training/ner_train.jsonl`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/ml_training/ner_train.jsonl) (5,000 annotated records).
* **Base Checkpoint:** `microsoft/deberta-v3-small` (or `roberta-base`).
* **Entities to Extract:**
  * `ITEM_TYPE` (e.g., `FLG`, `GATE VALVE`, `BLT`, `GSKT`)
  * `SIZE` (e.g., `4IN`, `DN100`, `4"`, `100MM`)
  * `PRESSURE_RATING` (e.g., `300#`, `CLASS 300`, `PN50`, `CL300`)
  * `METALLURGY` (e.g., `A105`, `SS316`, `ASTM A350 LF2`, `WCB`)
  * `FACING_END` (e.g., `WNRF`, `RTJ`, `BW`, `SW`, `FF`)
  * `STANDARD` (e.g., `ASME B16.5`, `API 6D`, `API 600`, `ASTM A193`)
* **Execution:** Train for 3 epochs using Hugging Face `Trainer` with character offset mapping (`return_offsets_mapping=True`). Save final model weights to `backend/app/ml/model_weights/ner_deberta/`.

#### Step 2: Feature Engineering & Normalization Pipeline (`backend/app/ml/ner_tagger.py`)
* **Function:** `extract_attributes(raw_description: str) -> ExtractedMaterialAttributes`
* **Feature Engineering & Normalization Rules:**
  * **Dimension Standardizer:** Convert imperial inches (`4"`, `4IN`, `4 INCH`) or DN codes (`DN100`) to metric millimeters float (`100.0`).
  * **Pressure Standardizer:** Strip `#`, `LB`, `CLASS`, or `PN` (`300#`, `300LB`, `CL300` $\rightarrow$ `300`).
  * **Taxonomy Mapper:** Map abbreviations to canonical enums (`FLG` + `WN` $\rightarrow$ `FLANGE_WELD_NECK`, `A105` $\rightarrow$ `ASTM_A105`).
  * **Regex Fallback Guardrail:** Implement regex heuristics as a high-speed fallback if raw descriptions contain cleanly formatted standard codes.
* **Contract Output:** Returns a validated Pydantic model instance (`ExtractedMaterialAttributes`).

---

### File Deliverables & Interface Contracts

Work inside `backend/app/ml/`:

```
backend/app/ml/
├── ner_tagger.py         # Tag extraction + feature engineering & regex normalizer
├── train_ner.py          # DeBERTa-v3 token classification training script
└── model_weights/        # Directory for saved NER checkpoints
```

**Interface Signature:**
```python
# ner_tagger.py
def extract_attributes(raw_description: str) -> ExtractedMaterialAttributes:
    """Runs token classification + feature engineering normalization to output a validated schema."""
    ...
```

---

### Team Collaboration & Handoffs
1. **From Samriddih & Ranvijay:** You receive raw extracted text strings from incoming documents, invoices, and database dumps.
2. **With Shourya:** Shourya handles BGE-M3 bi-encoder training (`train_biencoder.py`) and pairs with you to ensure embedding queries align with your normalized tokens.
3. **To Mayank & Shourya:** Your `extract_attributes()` function directly feeds the **Tier Distribution System** (`backend/app/matching/tolerance.py`) where Mayank and Shourya verify ASME/ASTM safety constraints.
