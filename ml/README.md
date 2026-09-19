# Samanvay-AI Machine Learning & Vision Pipeline (`ml/`)

The `ml/` directory houses the complete Artificial Intelligence, Natural Language Processing, Computer Vision, and Active Learning pipelines powering **Samanvay-AI**.

Indian public sector enterprises (IOCL, ONGC, GAIL, BPCL, HPCL) maintain millions of inventory line items across disparate ERP systems (SAP, Oracle, Maximo). Due to 40+ years of decentralized manual data entry, the same physical valve or pipe fitting is described using wildly divergent dialects, non-standard abbreviations, metric/imperial mixtures, or scanned paper Material Test Certificates (MTCs).

The `ml/` sub-system solves this multi-dialect semantic fragmentation through a multi-stage, air-gapped machine learning pipeline.

---

## 1. End-to-End Pipeline Architecture

```
[ Scanned Paper MTCs / PDFs ]             [ Raw ERP Text Descriptions ]
               │                                        │
               ▼                                        ▼
    ┌──────────────────────┐               ┌────────────────────────┐
    │  ml/vision/          │               │  ml/ner/               │
    │  • OCREngine         │               │  • DialectNormalizer   │
    │  • MTCParser         │               │  • SlotTagger          │
    │  • Chemistry Engine  │               │    (DeBERTa-v3)        │
    └──────────┬───────────┘               └───────────┬────────────┘
               │                                       │
               └───────────────────┬───────────────────┘
                                   │
                                   ▼
                   [ Structured PhysicalAttributes ]
                 (Size, Class, Grade, Sched, Trim, CE)
                                   │
                                   ▼
                   ┌───────────────────────────────┐
                   │  ml/embeddings/               │
                   │  • VectorEncoder (BGE-M3)     │
                   │  • SamanvayQdrantClient       │
                   └───────────────┬───────────────┘
                                   │
                     [ Top-K Semantic Candidates ]
                                   │
                                   ▼
                   ┌───────────────────────────────┐
                   │  ml/ranking/                  │
                   │  • CompatibilityRanker        │
                   │  • Subvector Feature Extractor│
                   │  • ShapExplainer              │
                   └───────────────┬───────────────┘
                                   │
                     [ Top Ranked Candidates ]
                                   │
                                   ▼
                   ┌───────────────────────────────┐
                   │  rules/ Deterministic Safety  │
                   └───────────────┬───────────────┘
                                   │
                                   ▼
                   ┌───────────────────────────────┐
                   │  ml/active_learning/          │
                   │  • Human-in-the-Loop Cache    │
                   │  • Golden Benchmarks Bootstrap│
                   └───────────────────────────────┘
```

---

## 2. Directory Structure & Subsystems

```
ml/
├── __init__.py               # Top-level ML module initializer
├── active_learning/          # Human-in-the-loop feedback & calibration
│   ├── bootstrapper.py       # Seeds active learning cache from golden benchmarks
│   └── cache.py              # In-memory vector-based human decision cache
├── embeddings/               # Dense representation & vector database
│   ├── qdrant_client.py      # Qdrant client wrapper for HNSW vector collections
│   └── vector_encoder.py     # BAAI/BGE-M3 1024-dimensional dense text encoder
├── ner/                      # Dialect normalization & Named Entity Recognition
│   ├── normalizer.py         # Unicode NFKC cleaning, regex dialector, domain expansion
│   └── slot_tagger.py        # Token-level slot extraction using DeBERTa-v3 architecture
├── ranking/                  # Neural reranking & explainability
│   ├── explainer.py          # SHAP-style attribution of ranking feature weights
│   ├── feature_extract.py    # Decomposes matches into 4 distinct physical subvectors
│   └── ranker.py             # Cross-Encoder neural pair scoring
└── vision/                   # Document AI & metallurgical certificate verification
    ├── chemistry.py          # Carbon equivalent, PREN, spectral heat validation
    ├── mtc_parser.py         # EN 10204 Type 3.1 inspection certificate parser
    └── ocr_engine.py         # Dual-path PDF parser (PyMuPDF fast path + PaddleOCR fallback)
```

---

## 3. Tech Stack & Dependencies

| Tool / Model | Version / Spec | Role & Why Chosen |
|---|---|---|
| **BAAI/BGE-M3** | `1024-dim` | Multilingual, multi-granular dense embedding model. Outperforms OpenAI text-embedding-3 on industrial terminology and abbreviation matching. |
| **Cross-Encoder** | `ms-marco-MiniLM` | Joint query-candidate attention reranker. Eliminates embedding cosine false positives. |
| **DeBERTa-v3-small** | HuggingFace / ONNX | Disentangled attention token classifier for high-accuracy slot tagging on noisy industrial strings. |
| **Qdrant** | `v1.12.0` | Production vector database with HNSW graphs, scalar quantization, and strict payload metadata filtering. |
| **PaddleOCR PP-OCRv4** | OpenVINO / CPU | Lightweight, highly accurate text detection and recognition for scanned mill certificates. |
| **PyMuPDF (fitz)** | `^1.24.0` | Ultra-fast direct digital PDF text/table stream extraction (5ms vs 500ms for full OCR). |
| **Polars** | `^0.20.0` | High-performance columnar data manipulation for fast batch feature extraction. |
| **SHAP** | `^0.44.0` | KernelExplainer for feature importance visualization. |

---

## 4. Theoretical Concepts for Machine Learning Practitioners

### 1. Dense Semantic Retrieval vs Inverted Indexes (BM25):
- BM25 relies on exact lexical overlap. If CPSE 1 writes `"VLV GT 4IN 300# WCB"` and CPSE 2 writes `"GATE VALVE 4\" 300LB CAST STEEL"`, BM25 scores low because terms like `"VLV"`, `"GT"`, and `"CAST STEEL"` have zero character overlap.
- Dense embeddings map both strings to adjacent coordinates in a 1024-dimensional continuous metric space where $\cos(\theta) > 0.92$.

### 2. Cross-Encoder Joint Attention vs Bi-Encoder Cosine:
- Bi-encoders embed query $q$ and candidate $c$ independently: $\text{score} = \cos(\mathbf{u}_q, \mathbf{v}_c)$.
- Cross-encoders concatenate both strings $[q, c]$ into a single transformer input, allowing all-to-all cross-attention across tokens. This captures subtle critical differences (e.g. `"CLASS 150"` vs `"CLASS 1500"`).

### 3. Human-in-the-Loop (HITL) Active Learning:
- When the similarity confidence score is marginal ($0.65 \le S \le 0.82$), Samanvay-AI routes the candidate to an engineering supervisor dashboard. The human decision is cached and bootstrapped back into the similarity lattice.

---

## 5. How to Run Unit & ML Tests

```bash
# Test NER slot extraction and dialect normalization
pytest tests/ml/test_ner.py -v

# Test OCR and MTC certificate parsing
pytest tests/unit/test_ocr_and_mtc.py -v

# Test chemical analysis & Carbon Equivalent calculations
pytest tests/unit/test_chemistry.py -v
```
