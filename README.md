# Samanvay-AI

### Sovereign Cross-CPSE Spare Parts Interoperability, Dynamic Compatibility & Mutual Aid Logistics Mesh
**Ministry of Petroleum & Natural Gas (MoPNG) | Smart India Hackathon (SIH26099)**

[![Python: 3.14+](https://img.shields.io/badge/Python-3.14%2B-blue.svg)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](backend/)
[![Next.js: 16](https://img.shields.io/badge/Next.js-16.3%20(React%2019)-black.svg)](frontend/)
[![Qdrant](https://img.shields.io/badge/Qdrant-v1.12.0-red.svg)](ml/embeddings/)
[![Neo4j: 5.20](https://img.shields.io/badge/Neo4j-5.20-008CC1.svg)](graph/)
[![Docker: 2.0.0-PROD](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](docker/)

---

## 1. Executive Summary

India's 5 major public sector oil, gas, and petrochemical enterprises (**IOCL, ONGC, BPCL, HPCL, GAIL**) collectively hold over **₹12,000–15,000 Crore** in maintenance, repair, and overhaul (MRO) spare parts. Simultaneously, unplanned refinery shutdowns and emergency unit trips cost Indian Public Sector Undertakings (PSUs) **₹5–20 Crore per day**, largely driven by lengthy 6–18 month OEM procurement lead times.

**Samanvay-AI** solves this systemic challenge through a sovereign, air-gapped, cross-CPSE mutual aid mesh. Without disrupting legacy ERP systems (SAP S/4HANA, Oracle ERP, Maximo), Samanvay-AI enables:
1. **Intelligent MTC & Catalog Intake**: Sub-50ms vector PDF extraction and OCR parsing of EN 10204 3.1/3.2 Material Test Certificates.
2. **Deterministic Physics & Safety Core**: 21 codified mechanical and metallurgical engineering standards (ASME, ASTM, API, TEMA, NACE, ISO) that maintain unilateral veto power over AI predictions.
3. **Dynamic Tri-Tier Compatibility**: Runtime material parity evaluation with zero static tier assumptions.
4. **Attribute-Level Commercial Privacy**: Commercial procurement pricing is strictly masked across enterprise boundaries.
5. **Real-Time Logistics Topology & Star Graph**: Neo4j 5.20 knowledge graph modeling 19 CPSE refinery depots across India, road tortuosity ($1.28\times$), transit hours, and carbon footprint ($CO_2$) savings.
6. **Sovereign Audit Ledger & CISF Pass**: Tamper-evident SHA-256 chained audit blocks with Merkle verification and 100% offline air-gapped SVG QR code gate passes.

For deep architectural specifications, see **[architecture.md](architecture.md)**.

---

## 2. Master Repository Navigation Directory

Every directory in **Samanvay-AI** is modular, isolated, and documented with its own standalone `README.md`. Use this master index to jump directly into specific module documentation:

```
Samanvay-AI/
├── backend/                      # FastAPI Gateway, Services & Concurrency Core
│   ├── app/                      # Application Layer Root
│   │   ├── api/                  # REST Controllers & Dependencies
│   │   │   └── routers/          # API Route Definitions (Match, Ingest, Requisition, etc.)
│   │   ├── core/                 # App Settings, Security, Hashing & Exceptions
│   │   ├── models/               # SQLAlchemy 2.0 Database ORM Models
│   │   ├── schemas/              # Pydantic Schemas & Transfer Objects
│   │   └── services/             # Business Logic (Requisitions, Audit, CDC, Seeder)
├── rules/                        # 21 Codified Mechanical Safety Standards Engine
│   ├── asme/                     # ASME B16.5, B16.34, B16.11, B16.47, B16.48, B16.20
│   ├── astm/                     # ASTM Metallurgy DAG, A193/A194 Fasteners, LME Cracking
│   ├── equipment/                # TEMA Heat Exchangers, API 2000 Tanks, C795 Insulation
│   ├── piping/                   # ASME B36.10M Schedules, API 5L Line Pipe, NACE MR0175
│   ├── rotating/                 # API 610 Pumps, API 682 Seals, API 618 Compressors, Motors
│   └── valves/                   # API 6D Bore, API 607 Fire-Safe, API 526 PSV, Trims
├── ml/                           # Machine Learning, Vision & NLP Pipeline
│   ├── active_learning/          # HITL Bootstrapping & Prediction Caching
│   ├── embeddings/               # BAAI/bge-m3 1024-dim Encoders & Qdrant HNSW Client
│   ├── ner/                      # Dialect Normalizer & DeBERTa Slot Tagger
│   ├── ranking/                  # Feature Extraction, XGBoost Ranker & TreeSHAP
│   └── vision/                   # Dual-Path OCR, Chemistry, IIW CE & MTC Parsers
├── graph/                        # Neo4j Knowledge Graph & Inter-Depot Logistics Topology
├── docker/                       # Container Infrastructure, Docker Compose & Init Scripts
│   └── init-db/                  # PostgreSQL Extensions (uuid-ossp, pgcrypto)
├── scripts/                      # Operational Daemons, Database Seeders & Smoke Tests
├── datasets/                     # Master 5,000-Item Catalogs & Golden Benchmarks
│   └── generators/               # Dialect Simulators & Dataset Generation Scripts
├── frontend/                     # Next.js 16 App Router, React 19 & Tailwind UI Portal
└── tests/                        # Comprehensive Automated Test Suites
    ├── api/                      # REST API Endpoints & Privacy Filtering Tests
    ├── integration/              # 150 Golden Benchmark Validation Tests
    ├── ml/                       # NLP Tokenization & Slot Tagging Tests
    └── unit/                     # Focused Math, Safety Tolerance & Hashing Tests
```

### Complete Subsystem README Links:

| Module / Layer | Path | Documentation Scope & Core Focus |
|---|---|---|
| **Backend Root** | [backend/README.md](backend/README.md) | FastAPI architecture, async lifecycle, router bindings, dependencies |
| **Backend App Core** | [backend/app/README.md](backend/app/README.md) | High-level application architecture and service decomposition |
| **API Controllers** | [backend/app/api/README.md](backend/app/api/README.md) | REST contract standards, HTTP status codes, tenant header auth |
| **API Routers** | [backend/app/api/routers/README.md](backend/app/api/routers/README.md) | Endpoint specifications: `/match`, `/inventory`, `/requisition`, `/graph`, `/audit`, `/ingest` |
| **Security & Config** | [backend/app/core/README.md](backend/app/core/README.md) | Chained SHA-256 hashing, HMAC gate seals, Pydantic settings, custom exceptions |
| **Relational Models** | [backend/app/models/README.md](backend/app/models/README.md) | PostgreSQL 16 schema: Inventory, Requisitions, Locks, Gate Passes, Audit, Outbox |
| **Pydantic Schemas** | [backend/app/schemas/README.md](backend/app/schemas/README.md) | Data transfer contracts, Dynamic Compatibility Tiers, privacy filtering schemas |
| **Core Services** | [backend/app/services/README.md](backend/app/services/README.md) | Pessimistic locking, audit chain verification, outbox CDC listeners, catalog seeder |
| **Rules Engine Root** | [rules/README.md](rules/README.md) | Master orchestrator, hard safety gate invariant, universal property scorecard |
| **ASME Rules** | [rules/asme/README.md](rules/asme/README.md) | Pressure classes, flange facings, cast iron ear cracking, Series A/B, gaskets |
| **ASTM Rules** | [rules/astm/README.md](rules/astm/README.md) | Metallurgy DAG, cryogenic brittle fracture, stud/nut pairing, Liquid Metal Embrittlement |
| **Equipment Rules** | [rules/equipment/README.md](rules/equipment/README.md) | TEMA heat exchangers, API 2000 tank vacuum collapse, ASTM C795 CUI chlorides |
| **Piping Rules** | [rules/piping/README.md](rules/piping/README.md) | ASME B36.10M wall schedules, API 5L PSL 1/2, NACE MR0175 sour duty ($\le 22$ HRC) |
| **Rotating Rules** | [rules/rotating/README.md](rules/rotating/README.md) | API 610 pumps, API 682 seal plans, API 618 valves, ISO 15 bearings, Ex d motors |
| **Valves Rules** | [rules/valves/README.md](rules/valves/README.md) | API 6D full vs reduced bore, API 607 fire-safe, API 526 PSV orifice, trim ladder |
| **ML Subsystem Root** | [ml/README.md](ml/README.md) | Multimodal AI pipeline: Fast-path OCR, dialect normalization, XGBoost ranking |
| **Active Learning** | [ml/active_learning/README.md](ml/active_learning/README.md) | HITL engineer feedback loops, prediction caching, synthetic bootstrapping |
| **Dense Embeddings** | [ml/embeddings/README.md](ml/embeddings/README.md) | BGE-M3 1024-dim dense representation, Qdrant HNSW cosine indexing |
| **NER & Dialects** | [ml/ner/README.md](ml/ner/README.md) | 40+ acronym CPSE dialect normalizer (IOCL, ONGC, metric SAP) and slot tagger |
| **Ranker & Scoring** | [ml/ranking/README.md](ml/ranking/README.md) | 4 domain subvectors, XGBoost ranking, TreeSHAP explainability |
| **Vision & OCR** | [ml/vision/README.md](ml/vision/README.md) | Dual-Path OCR ($<50$ms fast-path), IIW Carbon Equivalent ($CE$), PREN, MTC parsing |
| **Knowledge Graph** | [graph/README.md](graph/README.md) | Neo4j 5.20 star graph, 19 refinery depot GPS coords, Haversine, road tortuosity, $CO_2$ |
| **Docker Engine** | [docker/README.md](docker/README.md) | Multi-container compose (Postgres, Qdrant, Neo4j, Backend, Frontend, CDC worker) |
| **Database Init** | [docker/init-db/README.md](docker/init-db/README.md) | Initial SQL scripts, UUID v4 extension, `pgcrypto`, outbox triggers |
| **Scripts & Workers** | [scripts/README.md](scripts/README.md) | Standalone CDC worker, database seeder, live API verification smoke test |
| **Datasets Root** | [datasets/README.md](datasets/README.md) | Master inventory catalog (5,000 items), golden benchmarks, OCR payloads |
| **Dataset Generators** | [datasets/generators/README.md](datasets/generators/README.md) | Procedural synthetic ERP generator with realistic dialect noise and 15% sparsity |
| **Test Suite Root** | [tests/README.md](tests/README.md) | Test architecture, test running instructions, coverage reporting |
| **API Tests** | [tests/api/README.md](tests/api/README.md) | FastAPI TestClient integration tests for all 6 router controllers |
| **Integration Tests** | [tests/integration/README.md](tests/integration/README.md) | Parameterized validation against 150 ground-truth Golden Benchmarks |
| **ML Tests** | [tests/ml/README.md](tests/ml/README.md) | NER tokenization, dialect expansion, and slot tagging tests |
| **Unit Tests** | [tests/unit/README.md](tests/unit/README.md) | Deterministic unit tests: 21 safety modules, $CE_{\text{IIW}}$, logistics, hashing |

---

## 3. Technology Stack

| Subsystem | Technology | Version | Purpose |
|---|---|---|---|
| **API Gateway** | **FastAPI** | `^0.110.0` | High-performance asynchronous REST API framework |
| **Web Portal** | **Next.js / React** | `16.3 / 19.0` | Executive Command Center, MTC Review, Gate Pass UI |
| **Styling** | **Tailwind CSS** | `v4.0.0` | Industrial UI design system with print stylesheet support |
| **Relational DB** | **PostgreSQL** | `16-alpine` | ACID transactions, pessimistic locks, audit ledger, CDC outbox |
| **Vector Engine** | **Qdrant** | `v1.12.0` | 1024-dim HNSW cosine vector similarity search |
| **Knowledge Graph** | **Neo4j** | `5.20-community` | Multi-CPSE property star graph & transit topology |
| **Dense Embeddings** | **BAAI/bge-m3** | PyTorch / ONNX | 1024-dimensional multilingual industrial text representations |
| **Fast Path OCR** | **PyMuPDF (fitz)** | `^1.24.0` | Sub-50ms vector PDF direct text and table stream extraction |
| **Raster OCR** | **PaddleOCR / EasyOCR** | OpenCV / PIL | High-resolution 300 DPI deskewed scan extraction |
| **Machine Learning** | **XGBoost / LightGBM**| `^2.0.0` | Pairwise ranking cross-encoder with TreeSHAP explainability |
| **Packaging** | **uv** | `^0.12.0` | Fast Python package management and virtual environment tooling |

---

## 4. Quick Start: Running Locally

### Prerequisites
- **Docker Desktop** (running on Windows/Linux/macOS)
- **Python 3.14+** (managed via `uv` or standard Python)
- **Node.js 20+** & `npm`

---

### Option A: Hybrid Development Mode (Recommended for Development & Hot-Reload)

In Hybrid Mode, the database containers run in Docker, while the backend and frontend run natively for immediate hot-reloading.

#### 1. Start Database Infrastructure
```powershell
# In project root, launch Postgres, Qdrant, and Neo4j
docker compose -f docker/docker-compose.yml up -d postgres qdrant neo4j
```

Verify that all three databases are healthy:
```powershell
docker ps
```

#### 2. Configure Environment
```powershell
Copy-Item .env.example .env
```

#### 3. Seed Database & Vector Store
```powershell
# Seeds 5,000 items, Genesis audit blocks, and Qdrant embeddings
uv run python scripts/seed_database.py
```

#### 4. Launch FastAPI Backend Gateway (Terminal 1)
```powershell
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs (Swagger): **`http://localhost:8000/docs`**
- Healthcheck: **`http://localhost:8000/health`**

#### 5. Launch Next.js Web Portal (Terminal 2)
```powershell
cd frontend
npm install
npm run dev
```
- Web Application: **`http://localhost:3000`**

---

### Option B: Full Docker Deployment (Production Emulation)

To launch all services (Databases, Backend, Frontend, and CDC Worker) in Docker containers:

```powershell
docker compose -f docker/docker-compose.yml up -d --build
```

---

## 5. Manual Testing & Feature Walkthrough

Once running locally, open **`http://localhost:3000`** to test each feature manually:

### 1. Executive Command Center (`/`)
- **Interactive Geo Radar**: Click on any refinery depot dot on the Indian subcontinent map (e.g., *Panipat*, *Uran*, *Visakh*) to inspect local inventory counts and unlocked capital in real time.
- **Active Logistics Corridors**: Review active emergency consignments and pulse transit markers across National Highway corridors (NH-44, NH-16).

### 2. Smart Document Intake & MTC Review (`/upload`)
- Test using the 4 built-in production presets:
  - **Preset 1 (L&T Hazira ASTM A105 Flange)**: Fast-path vector extraction, $CE_{\text{IIW}} = 0.41\%$, `STANDARD_WELDABLE`, auto-approved.
  - **Preset 2 (BHEL Trichy Cryogenic Valve)**: A350 LF2 body, $CE = 0.45\%$ triggers `PREHEAT_REQUIRED`, Charpy impact at $-46^\circ\text{C}$ verified.
  - **Preset 3 (Pennar F316L Flange)**: Marine duty stainless steel, computes $\text{PREN} = 25.02$.
  - **Preset 4 (Vendor X Smudged Scan - Out of Spec)**: Degraded scan, out-of-spec carbon ($0.38\% > 0.35\%$), $CE = 0.67\%$, routes to **HITL Triage Queue**.
- Click **"Commit to Sovereign Ledger"** to append the certificate to the cryptographic chain.

### 3. Plant Stock Ledger & HITL Diff Triage (`/inventory`)
- **Surplus Broadcast Toggle**: Click **"Broadcast"** / **"Un-broadcast"** on any item to transition state between local reserve (`IN_STORAGE`) and peer-visible surplus (`IDLE_SURPLUS`).
- **HITL Triage Queue**: Navigate to the HITL tab to view side-by-side diffs between physical plant master records and MTC candidates with automated safety rule justifications.
- **Export**: Click **"Export CSV / SAP MM"** to generate an RFC 4180 inventory spreadsheet.

### 4. Pre-Purchase Semantic Radar (`/discover`)
- Search by engineering terms (e.g., `gate valve 150#` or `flange 300#`).
- Click **"Inspect Safety Rules"** on any candidate to inspect the **21-Rule Scorecard** evaluated against ASME B16.5, ASTM DAG, and API 600.
- Verify that commercial prices are masked (`PRICE MASKED`) across peer enterprises.
- Click **"Compose Requisition"** to submit an inter-CPSE transfer request.

### 5. Requisition Hub & CISF Digital Gate Pass (`/requests` and `/requests/[id]`)
- Confirm inbound supply requests to generate a statutory gate pass.
- Inspect the **Printable CISF Gate Pass**:
  - Live NavIC satellite telemetry simulation.
  - **100% Offline SVG QR Code**: Deterministic Version 2 bit-matrix with embedded SHA-256 seal.
  - Press `Ctrl+P` (or click **"Print CISF Gate Pass"**) to verify the clean print layout.

### 6. Sovereign Cryptographic Audit Trail (`/audit`)
- Inspect chronological ledger blocks, parent hash links ($H_{i-1} \to H_i$), and consensus witness nodes.
- Click **"Verify Merkle Chain"** to execute real-time anti-tamper integrity verification across all 1,842 blocks.

---

## 6. Verification & Automated Test Suites

To verify backend physics, safety rules, and CDC replication through the CLI:

```powershell
# 1. Run live API integration smoke test
uv run python scripts/verify_live_api.py

# 2. Run real-time PostgreSQL-to-Neo4j CDC verification test
uv run python scripts/test_live_cdc.py

# 3. Run all 150 Golden Benchmark test cases (Tier 1, Tier 2, and 21 fatal hazard traps)
uv run pytest tests/integration/test_benchmarks.py -v

# 4. Run the 21 deterministic engineering safety unit tests
uv run pytest tests/unit/test_tolerance.py -v

# 5. Run the complete test suite with coverage
uv run pytest tests/ --cov=backend/app --cov=rules --cov=ml --cov=graph
```

---

## 7. Key Operational Standards & Formulas

- **IIW Carbon Equivalent Formula**:
  $$CE_{\text{IIW}} = C + \frac{Mn}{6} + \frac{Cr + Mo + V}{5} + \frac{Ni + Cu}{15}$$
  - $CE \le 0.43\%$: Standard weldable without preheat.
  - $0.43\% < CE \le 0.48\%$: Minimum $100^\circ\text{C}$ preheat mandated per ASME Section IX.
  - $CE > 0.48\%$: High cracking risk; requires post-weld heat treatment.

- **Pitting Resistance Equivalent Number (PREN)**:
  $$\text{PREN} = \%Cr + 3.3(\%Mo) + 16(\%N)$$

- **BEE Freight Carbon Footprint**:
  $$\text{CO}_2\text{ Saved (kg)} = \text{Distance (km)} \times \text{Weight (Metric Tonnes)} \times 0.062\text{ kg CO}_2/\text{tonne-km}$$

- **Cryptographic Audit Block Hashing**:
  $$H_i = \text{SHA256}(H_{i-1} \parallel \text{block\_height} \parallel \text{actor\_id} \parallel \text{action} \parallel \text{timestamp} \parallel \text{payload\_json})$$
