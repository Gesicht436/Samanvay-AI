# Project Context: Samanvay-AI (BharatCodex)

**Target Tooling:** Antigravity CLI / Monorepo Initializer

**Problem Statement:** SIH26099 — AI-Driven Standardization and Harmonization of Material Codes Across CPSEs (MoPNG) | Smart India Hackathon 2026

**Runtime Baseline:** Python 3.14 (Unified Backend Baseline), Node.js 26 (Frontend)

---

## 1. Architectural Philosophy: Modular Python Monorepo

To maximize iteration velocity and eliminate multi-container networking drag during the hackathon, the system transitions from a distributed microservice footprint to a **contract-first modular monorepo**.

* **Unified Backend Runtime:** A single FastAPI service structured around modular domain routers (`/ingest`, `/match`, `/graph`, `/auth`). High-throughput ASME/ASTM engineering checks are implemented purely in vectorized Python (`Polars`/`NumPy`) and Pydantic rules to prevent build-chain failures.

* **Single Client Interface:** A unified enterprise desktop web portal built in `Next.js 16`. The mobile Android app is dropped from the scope to allow total focus on core MoPNG and CPSE procurement workflows.

* **Decoupled Data Tier:** PostgreSQL for relational state and audit logging, Qdrant for dense semantic vector retrieval, and Neo4j for hierarchical cross-CPSE ontology mapping.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        WEB PORTAL & DASHBOARD                          │
│               (Next.js 16, React 19, Tailwind CSS, shadcn/ui)          │
│       • Catalog Deduplication Studio   • HITL Triage Panel             │
│       • Procurement Analytics          • Knowledge Graph Visualizer    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                              REST / JSON
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      UNIFIED FASTAPI BACKEND ENGINE                    │
│                                                                        │
│  ┌───────────────────────┐ ┌───────────────────┐ ┌──────────────────┐  │
│  │   INGESTION & OCR     │ │  ML/NLP PIPELINE  │ │ DETERMINISTIC    │  │
│  │     (PaddleOCR,       │ │ (DeBERTa-v3 NER,  │ │ TOLERANCE RULES  │  │
│  │   PyMuPDF, Polars)    │ │  BGE-M3 Embeds)   │ │ (ASME/ASTM)      │  │
│  └──────────┬────────────┘ └─────────┬─────────┘ └─────────┬────────┘  │
│             │                        │                     │           │
│             └────────────────────────┼─────────────────────┘           │
│                                      ▼                                 │
│                      ORCHESTRATION & CONTRACT LAYER                    │
│                        (Pydantic v2 Models & RBAC)                     │
└──────────────┬───────────────────────┬──────────────────────┬──────────┘
               │                       │                      │
               ▼                       ▼                      ▼
      ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
      │   POSTGRESQL    │    │      NEO4J       │    │     QDRANT      │
      │  (Audit/Auth/   │    │ (Taxonomy/Equiv. │    │ (Dense Vector   │
      │   Transactions) │    │      Graph)      │    │  SKU Index)     │
      └─────────────────┘    └──────────────────┘    └─────────────────┘

```

---

## 2. Core Functional Pipeline

* **Stage 1: Multi-Modal Ingestion & Digitization**
Ingests unstandardized ERP dumps (SAP MM `.xlsx`/`.csv`), scanned delivery challans, and Mill Test Certificates (MTCs). PyMuPDF extracts text directly from digital PDFs, while PaddleOCR (PP-OCRv4) handles rotated, low-quality scanned certificates and plant equipment nameplates.

* **Stage 2: Slot-Filling NER & Semantic Vector Retrieval**
Domain-adapted `DeBERTa-v3-small` / `RoBERTa-base` token classification isolates critical mechanical slots (Nominal Bore, Pressure Class, Metallurgy, Facing, Standard) into normalized Pydantic schemas. Concurrently, a fine-tuned `BAAI/bge-m3` bi-encoder projects messy vendor strings into a 1024-dimensional space and queries Qdrant for the top 10 candidate matches ($<15\text{ ms}$).

* **Stage 3: Deterministic Tolerance Verification (ASME / ASTM Rules)**
A pure-Python rule engine evaluates candidates against strict engineering invariants (zero-tolerance size matching, unidirectional pressure rating rules, and ASTM metallurgy upgrade allowances). Candidates are classified into **Tier-1 (Identical)**, **Tier-2 (Substitute)**, and **Tier-3 (Incompatible)**.

* **Stage 4: Knowledge Graph Traversal & Enterprise Reconciliation**
Neo4j links approved items to canonical entities mapped to UNSPSC v26 and GeM (Government e-Marketplace) taxonomies. Cross-CPSE queries identify identical idle spare parts across sister depots (e.g., IOCL Panipat requesting an item that is sitting idle at an ONGC Hazira warehouse).

* **Stage 5: Human-in-the-Loop (HITL) Procurement Dashboard**
A Next.js 16 portal surfaces deduplication results, allows procurement officers to review and resolve ambiguous matches ($70\% - 90\%$ confidence), and visualizes potential capital freed across CPSEs.

---

## 3. Team Work Distribution & Ownership Matrix

| Member | Primary Role | Active Directory | Core Responsibilities | Technology Stack |
| --- | --- | --- | --- | --- |
| **Mayank Anand** | Team Lead, System Architect & Tier Distribution Lead | `backend/app/api/`, `backend/app/contracts/`, `backend/app/matching/` | Monorepo structure, Pydantic v2 contracts, API Gateway routes, Docker orchestration, frontend-backend API connections, Tier Distribution System (deterministic ASME/ASTM tolerance engine with Shaurya), and Qdrant collaboration. | FastAPI, SQLAlchemy, Docker Compose, Pydantic v2, Python |
| **Hariom** | Machine Learning Lead (NER & Feature Engineering) | `backend/app/ml/` | Feature engineering, DeBERTa-v3 slot-filling NER training & token classification inference for physical specs (size, rating, metallurgy, standard). | PyTorch, Hugging Face Transformers, Token Classification, Python |
| **Harsh** | Knowledge Graph Lead (Neo4j) | `backend/app/graph/` | Full Neo4j lifecycle: database setup, Cypher constraints, taxonomy seeding (`seed_graph.py` from UNSPSC/GeM/Master), and cross-CPSE spare-locator traversals. | Neo4j Python Bolt Driver, Cypher, Graph Database, Docker |
| **Samriddih** | Document Intelligence & OCR Lead | `backend/app/ingestion/` | Dual-path document parsing (PyMuPDF fast path), PaddleOCR image extraction for scanned MTCs/challans, text normalization, and certificate key-value layout extraction. | Python, PaddleOCR (PP-OCRv4), PyMuPDF (`fitz`), Pillow |
| **Shaurya** | Data Pipelines, Semantic Matching & Float Support | `data/`, `backend/app/ml/`, `backend/app/matching/` | BGE-M3 bi-encoder fine-tuning for semantic matching (helping Hariom), Qdrant vector database collaboration with Mayank, Tier Distribution System assistance with Mayank, golden benchmark suite, and floating support. | Sentence-Transformers, Qdrant Client, Pandas, Polars, JSON Lines |
| **Ranvijay** | Frontend Developer & Ingestion Storage | `frontend/`, `backend/app/ingestion/` | Central Next.js 16 procurement portal (Deduplication Studio, HITL Review Panel, Analytics Dashboard), and collaborating with Samriddih to persist extracted OCR document text into PostgreSQL via SQLAlchemy. | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, PostgreSQL, SQLAlchemy |

---

## 4. Repository Layout

```
samanvay-ai/
├── .env.example
├── docker-compose.yml              # PostgreSQL, Neo4j, Qdrant, and unified FastAPI backend
├── Makefile                        # Dev commands: make dev, make test, make seed-data
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── requirements.txt            # fastapi, uvicorn, pydantic, sqlalchemy, torch, neo4j, qdrant-client
│   └── app/
│       ├── main.py                 # Core FastAPI application
│       ├── config.py               # Application settings and environment configuration
│       │
│       ├── contracts/              # Pydantic v2 schemas: single source of truth
│       │   ├── material.py         # ExtractedMaterialAttributes, CanonicalItem
│       │   ├── matching.py         # MatchResult, EquivalenceTier enum
│       │   └── taxonomy.py         # UNSPSC and GeM schemas
│       │
│       ├── ingestion/              # Module: Document & OCR Intake (Smariddih)
│       │   ├── ocr_engine.py       # PaddleOCR wrapper (angle detection & box reconstruction)
│       │   ├── pdf_parser.py       # Dual-path router: PyMuPDF vs. image rendering
│       │   └── certificate.py      # MTC key-value tabular extraction
│       │
│       ├── ml/                     # Module: Industrial ML & Search (Hariom)
│       │   ├── ner_tagger.py       # DeBERTa-v3 token classification inference & regex normalizer
│       │   ├── vector_search.py    # BGE-M3 embedding generation & Qdrant query client
│       │   ├── train_ner.py        # Token classification training script
│       │   ├── train_biencoder.py  # Contrastive learning script (MultipleNegativesRankingLoss)
│       │   └── model_weights/      # Directory for saved model checkpoints
│       │
│       ├── matching/               # Module: Deterministic Rule Engine (Harsh)
│       │   ├── asme_rules.py       # ASME B16.5 & ASTM alloy tolerance lookup matrices
│       │   └── tolerance.py        # Deterministic constraint validation & tier assignment
│       │
│       ├── graph/                  # Module: Neo4j Knowledge Graph (Harsh)
│       │   ├── client.py           # Neo4j Bolt driver connection pooling
│       │   ├── queries.py          # Cypher cross-CPSE spare reconciliation traversals
│       │   └── seed_graph.py       # Neo4j taxonomy seeding script
│       │
│       └── api/                    # Module: Gateway API Routes (Mayank)
│           ├── v1/
│           │   ├── ingest.py       # Document & batch CSV upload endpoints
│           │   ├── match.py        # Matching, reconciliation & HITL triage endpoints
│           │   └── graph.py        # Knowledge graph visualizer data endpoints
│           └── deps.py             # Database and service session dependencies
│
├── frontend/                       # Central Web Portal (Ranvijay)
│   ├── package.json
│   ├── next.config.mjs
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── src/
│       ├── app/
│       │   ├── layout.tsx          # App shell, persistent enterprise navigation
│       │   ├── dashboard/page.tsx  # Procurement metrics & unlocked working capital
│       │   ├── deduplication/page.tsx # Batch file ingestion studio
│       │   └── hitl/page.tsx       # Side-by-side HITL match validation panel
│       ├── components/
│       │   ├── ui/                 # shadcn/ui components (cards, badges, tables, dialogs)
│       │   └── ItemComparisonCard.tsx # Reconciliation side-by-side comparison widget
│       └── lib/
│           ├── api.ts              # API client communicating with backend gateway
│           ├── types.ts            # TypeScript interfaces aligned with backend Pydantic schemas
│           └── mockData.ts         # Fallback data for offline UI development
│
└── data/                           # Data Factory & Curation (Shaurya)
    ├── generate_catalogs.py        # Combinatorial CPSE mock catalog generator (10k items)
    ├── build_train_sets.py         # Formatter for NER BIO tags and MNRL contrastive pairs
    ├── curate_taxonomies.py        # Formatter for UNSPSC v26 and GeM category tables
    ├── mock_cpes_catalogs/         # Output: Synthetic IOCL, ONGC, and BPCL catalog CSVs
    ├── ml_training/                # Output: ner_train.jsonl & biencoder_pairs.jsonl
    ├── taxonomies/                 # Output: Clean CSVs for Neo4j seeding (UNSPSC, GeM)
    └── raw/                        # Output: Sample MTC PDFs & challan images

```

---

## 5. Execution Directives for Tooling & Bootstrapping

1. **Deterministic Python Implementation:** Verify that all matching logic, ASME constraints, and matrix lookups are implemented in pure Python (`Polars`/`NumPy`); ensure no references to CMake, `pybind11`, or native C++ extension builds remain.

2. **Strict Python Version Pinning:** Configure `backend/Dockerfile` and local environments to Python 3.11 or 3.12 to preserve binary wheel stability across `torch`, `paddleocr`, and `transformers`.

3. **Data-Driven Unblocking:** Execute `data/generate_catalogs.py` immediately to populate `data/mock_cpes_catalogs/` and `data/ml_training/` with seed fixtures, allowing backend, ML, graph, and frontend engineers to build and test asynchronously.
