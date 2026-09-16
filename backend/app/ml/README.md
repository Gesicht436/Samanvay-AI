# Machine Learning, NLP & Semantic Search (`backend/app/ml`)

## 1. Overview
The `ml` package handles text normalization, slot-filling Named Entity Recognition (NER), refinery dialect expansion, and dense vector semantic search across multi-enterprise material catalogs.

The primary objective of this module is to transform messy, abbreviated, free-text procurement descriptions from IOCL, ONGC, and BPCL into structured, typed physical properties, and retrieve high-probability candidate matches from the 2,200-item Canonical Master Catalog in under 15 milliseconds.

---

## 2. Directory Structure

```
backend/app/ml/
|-- model_weights/               # Local model checkpoints and tokenizer files
|   `-- README.md                # Weights directory guide
|-- __init__.py                  # Public exports for the ML package
|-- ner_tagger.py                # Pre-compiled regex slot-filling NER and attribute extractor
|-- train_biencoder.py           # Training pipeline for dense bi-encoder embeddings with dev eval
|-- train_ner.py                 # Training script for sequence labeling NER models
|-- vector_search.py             # Attribute-filtered Qdrant retrieval with in-memory fallback
`-- README.md                    # This file
```

---

## 3. Attribute Extraction & NER Normalization (`ner_tagger.py`)

Industrial procurement descriptions in Indian CPSEs are concise, heavily abbreviated, and use non-standard conventions. `ner_tagger.py` transforms these raw strings into clean, typed `ExtractedMaterialAttributes` objects.

### A. Performance Optimizations & Architecture

1. **Pre-Compiled Regular Expressions**:
   Over 40 regular expression patterns (item types, facing ends, pressure classes, metallurgies, standards, and rotating equipment specifications) are compiled once at module import time (`re.compile`) rather than re-compiled on every function call. This eliminates repeated compilation overhead across high-throughput API endpoints.

2. **Pre-Compiled Thesaurus Expansion**:
   Refinery shorthand patterns in `REFINERY_THESAURUS` are pre-compiled at module load time. The `expand_refinery_thesaurus()` function applies substitution passes over the text without dynamic regex compilation.

3. **Unicode & Whitespace Normalization (`normalize_text`)**:
   Before parsing, descriptions undergo a standardized normalization pass:
   - Unicode NFKC normalization to resolve ligatures, full-width characters, and non-standard symbols.
   - Removal of non-printable control characters.
   - Collapsing consecutive tabs, spaces, and newlines into single spaces.
   - Conversion to uppercase for predictable pattern matching.

4. **Early Thesaurus Expansion Pipeline**:
   Thesaurus expansion executes *before* regex token extraction. For example, when the acronym `NRV` is encountered, it is immediately expanded to `CHECK VALVE`. Subsequent item type heuristics match `CHECK VALVE` directly, eliminating the need for redundant pattern duplication.

5. **In-Memory LRU Caching**:
   The main extraction function `@lru_cache(maxsize=2048)` caches extracted attribute objects by exact input string. When processing bulk batches containing repeated items, deduplication scans, or high-frequency search queries, extraction resolves in O(1) time.

### B. Physical Unit Normalization

1. Imperial to Metric Nominal Bore:
   - `1/2"`, `0.5"`, `15 NB` -> `15.0 mm` (`size_inch = '1/2"'`, `dn_code = 'DN15'`)
   - `1"`, `25 NB` -> `25.0 mm` (`size_inch = '1"'`, `dn_code = 'DN25'`)
   - `2"`, `50 NB` -> `50.0 mm` (`size_inch = '2"'`, `dn_code = 'DN50'`)
   - `4"`, `100 NB` -> `100.0 mm` (`size_inch = '4"'`, `dn_code = 'DN100'`)
   - `6"`, `150 NB` -> `150.0 mm` (`size_inch = '6"'`, `dn_code = 'DN150'`)
   - `8"`, `200 NB` -> `200.0 mm` (`size_inch = '8"'`, `dn_code = 'DN200'`)
   - `12"`, `300 NB` -> `300.0 mm` (`size_inch = '12"'`, `dn_code = 'DN300'`)

2. Metric Pressure (PN) to ASME Pressure Class:
   - `PN 20` -> `Class 150`
   - `PN 50` -> `Class 300`
   - `PN 100` -> `Class 600`
   - `PN 150` -> `Class 900`
   - `PN 250` -> `Class 1500`
   - `PN 420` -> `Class 2500`

### C. Refinery Shorthand & Dialect Thesaurus

`expand_refinery_thesaurus` expands common CPSE acronyms:
- `NRV`: Non-Return Valve -> `CHECK VALVE` (Governed by API 6D / BS 1868)
- `BFV`: Butterfly Valve -> `BUTTERFLY VALVE` (Governed by API 609)
- `GV`: Gate Valve -> `GATE VALVE` (Governed by API 600)
- `GLV`: Globe Valve -> `GLOBE VALVE` (Governed by BS 1873)
- `PLUG VLV`: Plug Valve -> `PLUG VALVE` (Governed by API 599)
- `CV` / `CONTROL VLV`: Control Valve -> `CONTROL VALVE`
- `PSV` / `SRV` / `RV`: Pressure Safety / Relief Valve -> `PRESSURE SAFETY VALVE`
- `RED` / `RDCR`: Reducer Pipe Fitting -> `REDUCER`
- `SPRF`: Spectacle Blind Raised Face -> `FLANGE_BLIND` with `RF` facing
- `THRF`: Threaded Flange Raised Face -> `FLANGE_SLIP_ON` with `THRD` and `RF`
- `CS`: Carbon Steel -> `ASTM A105`
- `LTCS`: Low Temperature Carbon Steel -> `ASTM A350 LF2`
- `DSS`: Duplex Stainless Steel -> `ASTM A182 F51` (UNS S31803)
- `SDSS`: Super Duplex Stainless Steel -> `ASTM A815 S32750` / `ASTM A182 F53`
- `INCO 625`: Inconel 625 Nickel-Chromium Alloy (UNS N06625)
- `HAST-C`: Hastelloy C-276 Nickel-Molybdenum-Chromium Alloy (UNS N10276)
- `MONEL 400`: Monel 400 Nickel-Copper Alloy (UNS N04400)
- `IBR`: Indian Boiler Regulations (1950) -> sets `is_ibr_certified = True`

### D. Rotating & Electrical Attribute Parsing

- **Electric Motors**: Extracts power in kilowatts (`37 KW`) or converts horsepower (`50 HP * 0.7457 = 37.3 KW`). Infers motor poles and rotational speed (2P = 3000 RPM, 4P = 1500 RPM, 6P = 1000 RPM). Parses flameproof enclosure certifications (`Ex d IIC T4`, `Ex e`, `Non-Ex`).
- **Mechanical Seals**: Identifies API 682 piping flush plans (`Plan 11`, `Plan 23`, `Plan 52`, `Plan 53A`, `Plan 54`) and sleeve bore diameters.
- **Bearings**: Extracts ISO 15 series codes (`6210` -> 50mm bore, `6312` -> 60mm bore) and radial clearance designations (`C2`, `C3`, `C4`, `CN`, `C0`).
- **Centrifugal Pumps**: Extracts design volumetric flow rate (`M3/HR`) and differential head (`M`).

---

## 4. Semantic Vector Retrieval (`vector_search.py`)

### The Hybrid Retrieval Strategy

Rather than relying purely on keyword matching, `vector_search.py` performs dense semantic vector search:

1. **Attribute-Enriched Vector Query Construction**:
   The search query is augmented with extracted technical tokens (`ITEM_FLANGE_WELD_NECK SIZE_100.0 CLASS_300 MAT_ASTM_A105 FACE_RF QUERY: ...`). This mirrors the indexing format used when the Canonical Master Catalog was created, maximizing cosine similarity alignment.

2. **Attribute-Aware Payload Pre-Filtering**:
   When `ner_tagger.py` extracts an `item_type` with confidence >= 0.4, `get_candidate_skus()` applies a Qdrant payload pre-filter. For instance, a flange query searches exclusively among the ~300 flange entries rather than the full 2,200 catalog items. This reduces the Approximate Nearest Neighbor (ANN) search space while eliminating cross-category false candidates.

3. **Resilient Empty-Result Fallback**:
   If a filtered search returns zero results (for example, if a query contains an edge-case item type not directly categorized in the master), the system automatically retries with an unfiltered vector query, guaranteeing zero search regressions.

4. **Explicit Filtered Query API (`get_candidate_skus_filtered`)**:
   Provides an explicit filtering interface allowing downstream services (such as the Human-in-the-Loop resolution interface) to retrieve candidates constrained to specific item types or pressure classes.

5. **Deterministic Offline Embedder Fallback**:
   If PyTorch or transformer weights are unavailable in a restricted offline environment, the system automatically uses `DeterministicFeatureEmbedder` (a 1024-dimensional normalized HashingVectorizer), ensuring 100% offline functionality.

6. **In-Memory Qdrant Fallback**:
   If the live Qdrant container is unreachable, the client initializes an in-memory Qdrant instance (`QdrantClient(":memory:")`), keeping local tests and micro-benchmarks fully operational without external infrastructure.

---

## 5. Model Training Pipelines

### 1. Bi-Encoder Training (`train_biencoder.py`)

Fine-tunes a dense sentence-transformer model (`BAAI/bge-m3`) using Multiple Negatives Ranking Loss (MNRL) on 8,000 CPSE contrastive pairs:
- Anchor: `FLG WNRF 4IN 300# A105` (IOCL)
- Positive: `FLANGE WELD NECK 4" CL300 ASTM A105 RF` (ONGC)
- Hard Negative: `FLG WNRF 4IN 150# A105` (Dangerous pressure mismatch)

**Key Features**:
- **Train/Dev Splitting**: Partitions training data into 90% training and 10% held-out validation sets.
- **Dev-Set Cosine Evaluation**: Evaluates cosine similarity using `EmbeddingSimilarityEvaluator` at the conclusion of each epoch and automatically retains the best checkpoint.
- **Hardware Acceleration**: Configured for CUDA FP16 automatic mixed precision.

### 2. NER Token Classifier Training (`train_ner.py`)

Fine-tunes a DeBERTa-v3 token classification transformer on 5,000 annotated industrial procurement records to identify BIO entity spans:
- `B-ITEM_TYPE`, `I-ITEM_TYPE`
- `B-SIZE`, `I-SIZE`
- `B-PRESSURE_RATING`, `I-PRESSURE_RATING`
- `B-METALLURGY`, `I-METALLURGY`
- `B-FACING_END`, `I-FACING_END`
- `B-STANDARD`, `I-STANDARD`

**Key Features**:
- Character-to-subword offset mapping for precise entity boundary alignment.
- Compatible with modern `transformers` (v4.41+) using `eval_strategy="epoch"`.
- Checkpoints saved to `backend/app/ml/model_weights/deberta_ner_cpes/`.

---

## 6. Public API Reference

The `backend/app/ml` package exports the following primary functions via `__init__.py`:

```python
from backend.app.ml import (
    extract_attributes,          # Extracts structured ExtractedMaterialAttributes
    expand_refinery_thesaurus,   # Expands CPSE shorthand terms to standardized phrases
    normalize_text,              # Normalizes whitespace, unicode, and control characters
    get_qdrant_client,           # Returns singleton QdrantClient (live or in-memory)
    get_candidate_skus,          # Retrieves top-K candidates with automatic payload filtering
    get_candidate_skus_filtered, # Retrieves candidates with explicit attribute filters
    seed_canonical_catalog,      # Indexes 2,200 canonical master materials into Qdrant
)
```
