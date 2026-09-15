# Machine Learning, NLP & Semantic Search (`backend/app/ml`)

## 1. Overview
The `ml` package handles text normalization, slot-filling Named Entity Recognition (NER), refinery dialect expansion, and dense vector semantic search across multi-enterprise material catalogs.

---

## 2. Directory Structure

```
backend/app/ml/
|-- model_weights/               # Local model checkpoints and tokenizer files
|   `-- README.md                # Weights directory guide
|-- ner_tagger.py                # Regex slot-filling NER and attribute extractor
|-- train_biencoder.py           # Training pipeline for dense bi-encoder embeddings
|-- train_ner.py                 # Training script for sequence labeling NER models
|-- vector_search.py             # Qdrant vector retrieval with in-memory fallback
`-- README.md                    # This file
```

---

## 3. Attribute Extraction & NER Normalization (`ner_tagger.py`)

Industrial procurement descriptions in Indian CPSEs are concise, heavily abbreviated, and use non-standard conventions. `ner_tagger.py` transforms these raw strings into clean, typed `ExtractedMaterialAttributes` objects.

### A. Physical Unit Normalization
1. Imperial to Metric Nominal Bore:
   - `1/2"`, `0.5"`, `15 NB` -> `15.0 mm`
   - `1"`, `25 NB` -> `25.0 mm`
   - `2"`, `50 NB` -> `50.0 mm`
   - `4"`, `100 NB` -> `100.0 mm`
   - `6"`, `150 NB` -> `150.0 mm`
2. Metric Pressure (PN) to ASME Pressure Class:
   - `PN 20` -> `Class 150`
   - `PN 50` -> `Class 300`
   - `PN 100` -> `Class 600`
   - `PN 150` -> `Class 900`
   - `PN 250` -> `Class 1500`
   - `PN 420` -> `Class 2500`

### B. Refinery Shorthand & Dialect Thesaurus
`expand_refinery_thesaurus` expands common CPSE acronyms:
- `NRV`: Non-Return Valve -> `CHECK_VALVE`
- `BFV`: Butterfly Valve -> `BUTTERFLY_VALVE` (Governed by API 609)
- `GV`: Gate Valve -> `GATE_VALVE` (Governed by API 600)
- `GLV`: Globe Valve -> `GLOBE_VALVE` (Governed by BS 1873)
- `PLUG VLV`: Plug Valve -> `PLUG_VALVE` (Governed by API 599)
- `SPRF`: Spectacle Blind Raised Face -> `FLANGE_BLIND` with `RF` facing
- `THRF`: Threaded Flange Raised Face -> `FLANGE_SLIP_ON` with `THRD` and `RF`
- `CS`: Carbon Steel -> `ASTM A105`
- `LTCS`: Low Temperature Carbon Steel -> `ASTM A350 LF2`
- `DSS`: Duplex Stainless Steel -> `ASTM A182 F51` (2205)
- `SDSS`: Super Duplex Stainless Steel -> `ASTM A815 S32750` / `A182 F53`
- `INCO 625`: Inconel 625 Nickel Alloy
- `HAST-C`: Hastelloy C-276 Nickel-Molybdenum-Chromium Alloy
- `MONEL 400`: Monel 400 Nickel-Copper Alloy
- `IBR`: Indian Boiler Regulations (1950) -> sets `is_ibr_certified = True`

### C. Rotating & Electrical Attribute Parsing
- Power: Extracts kilowatts (`37 KW`) or converts horsepower (`50 HP * 0.7457 = 37.3 KW`).
- Speed and Poles: Infers pole count (2P = 3000 RPM, 4P = 1500 RPM, 6P = 1000 RPM).
- Hazardous Certification: Identifies flameproof ratings (`Ex d IIC T4`, `Ex e`, `Non-Ex`).
- Mechanical Seal Flush Plans: Identifies API 682 piping plans (`Plan 11`, `Plan 53A`).
- Bearings: Extracts ISO 15 series codes (`6210` -> 50mm bore, `6312` -> 60mm bore) and radial clearance (`C3`, `C4`, `CN`).

---

## 4. Semantic Vector Retrieval (`vector_search.py`)

### The Hybrid Retrieval Strategy
Rather than relying purely on text keywords, `vector_search.py` performs dense semantic vector search:
1. Candidate Search: Encodes the query into a high-dimensional dense vector and queries the Qdrant vector database to retrieve the top 5 to 20 candidate SKUs in under 15 milliseconds.
2. In-Memory Fallback: If the external Qdrant instance is offline, the module automatically activates an in-memory cosine similarity search over the pre-embedded Canonical Master Catalog, ensuring 100% offline usability during testing.
3. Candidate Hand-off: Retrieved candidates are forwarded directly to `tolerance.py` for deterministic safety validation.

---

## 5. Model Training Pipelines

### 1. Bi-Encoder Training (`train_biencoder.py`)
Fine-tunes a Sentence-Transformers model (`all-MiniLM-L6-v2`) on CPSE triplets:
- Anchor: `FLG WNRF 4IN 300# A105` (IOCL)
- Positive: `FLANGE WELD NECK 4" CL300 ASTM A105 RF` (ONGC)
- Hard Negative: `FLG WNRF 4IN 150# A105` (Dangerous pressure mismatch)
This trains the embedding space to separate items that differ by safety-critical parameters.

### 2. NER Token Classifier Training (`train_ner.py`)
Fine-tunes a token classification transformer to extract entity spans (`B-SIZE`, `I-SIZE`, `B-PRESSURE`, `B-ALLOY`, `B-FACING`) from raw ERP lines.
