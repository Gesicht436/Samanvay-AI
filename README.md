# Samanvay-AI (BharatCodex #81)
## Unified Material Code Standardization & Cross-CPSE Surplus Inventory Discovery Platform
### Ministry of Petroleum & Natural Gas (MoPNG)

---

## 1. Overview and Problem Statement

### The Industrial Challenge
India's primary public sector energy enterprises—Indian Oil Corporation Limited (IOCL), Oil and Natural Gas Corporation (ONGC), and Bharat Petroleum Corporation Limited (BPCL)—procure millions of specialized industrial components annually. These include high-pressure piping, valves, flanges, pumps, flameproof electric motors, and mechanical seals.

For decades, each organization has operated isolated Enterprise Resource Planning (ERP) systems (such as SAP MM, Oracle ERP, and IBM Maximo). As a result, identical physical components are cataloged under disparate naming conventions:

- IOCL Catalogue Description: `FLG WNRF 4IN 300# A105`
- ONGC Catalogue Description: `FLANGE WELD NECK 4" CL300 ASTM A105 RF`
- BPCL Catalogue Description: `FLG-WN-DN100-PN50-CS-RF`

Because traditional databases rely on exact string equality, systems treat these three entries as unrelated items. This creates severe inefficiencies:

1. Duplicate Procurement: A refinery purchases a component from international suppliers with lead times of 180 to 240 days, while a sister facility less than 100 kilometers away holds identical surplus stock idle.
2. Capital Lock-in: Hundreds of crores in working capital remain tied up in redundant inventory across depots.
3. Safety Risks: Non-technical staff may mistake superficially similar components as interchangeable. In high-pressure hydrocarbon service, substituting an incompatible pressure class or material grade can cause catastrophic pipeline rupture.

### How Samanvay-AI Solves This
Samanvay-AI provides an automated, sovereign reconciliation pipeline:
- Parses unstructured ERP procurement strings, PDF purchase orders, and scanned Mill Test Certificates (MTCs).
- Normalizes proprietary naming conventions into canonical physical attributes (Nominal Bore, Pressure Rating, ASTM Metallurgy, Facing, and Pipe Schedule).
- Performs sub-15ms semantic candidate retrieval via dense vector search.
- Validates compatibility using a deterministic safety engine based on ASME, ASTM, API, and Indian Boiler Regulations (IBR 1950) standards.
- Dynamically reranks inventory using real-time human feedback without requiring machine learning model retraining.
- Exposes cross-depot surplus discovery, GIS-based freight estimation, and digital CISF material gate pass issuance.

---

## 2. High-Level System Architecture

```
                       RAW PROCUREMENT INPUTS
     ERP Descriptions | PDF Delivery Challans | Scanned Mill Test Certificates
                                |
                                v
               [1. INGESTION & DOCUMENT PARSING]
        Windows Media OCR (winocr) | PaddleOCR | PDFPlumber
        Extracts raw text, tabular heat numbers, and chemistry
                                |
                                v
                [2. ML NORMALIZATION & NER TAGGER]
        CPSE Shorthand Thesaurus (NRV, BFV, SPRF, LTCS, DSS)
        Extracts: Size (mm/inch), Pressure Class, ASTM Metallurgy
                                |
                                v
              [3. SEMANTIC VECTOR CANDIDATE RETRIEVAL]
        Dense Bi-Encoder / Feature Embedding Search (<15ms)
        Qdrant Vector Database Candidate Filtering
                                |
                                v
              [4. DETERMINISTIC SAFETY TOLERANCE ENGINE]
        ASME B16.5 & B16.34 Pressure Ladders | ASTM DAG Metallurgy
        NACE MR0175 Sour Service | IBR 1950 Indian Boiler Rules
        Pipe Schedules (B36.10M) | ASME B16.47 Series A vs B
                                |
                                v
               [5. ACTIVE LEARNING DYNAMIC RERANKER]
        Dual-indexed in-memory feedback cache
        Prioritizes expert approvals | Demotes rejected traps
                                |
                                v
                 [6. GRAPH ONTOLOGY & LOGISTICS]
        Neo4j Graph (UNSPSC v26 & GeM Taxonomies)
        GIS Multi-Depot Haversine Distance & Freight Calculator
        Atomic Inventory Locks | Digital CISF Gate Pass
                                |
                                v
                 [7. ENTERPRISE WEB APPLICATION]
        Next.js 16 Web Portal (Dashboard, Deduplication, HITL,
        Transfers, Sovereign Audit Ledger, Excel CSV Export)
```

---

## 3. Directory Layout

```
Samanvay-AI/
|-- backend/                     # Python 3.14 FastAPI application
|   |-- app/
|   |   |-- api/                 # API router definitions and dependencies
|   |   |   `-- v1/              # Endpoint modules: match, requisition, ingest, graph, audit
|   |   |-- contracts/           # Pydantic v2 data models and type definitions
|   |   |-- graph/               # Neo4j graph client, Cypher queries, and seed data
|   |   |-- ingestion/           # OCR engine, PDF parsers, and SQLite/Postgres storage
|   |   |   `-- data_pipeline/   # Catalog loaders and document seeding utilities
|   |   |-- matching/            # ASME/ASTM rules, logistics calculations, and active learning
|   |   |-- ml/                  # NER slot-filler, dialect thesaurus, and vector search
|   |   |   `-- model_weights/   # Local model weights and transformer configuration
|   |   |-- config.py            # Global application settings and environment variables
|   |   `-- main.py              # FastAPI entrypoint, middleware, and lifecycle handlers
|   `-- README.md                # Backend architecture and setup documentation
|
|-- frontend/                    # Next.js 16 React web application
|   |-- src/
|   |   |-- app/                 # App Router pages (dashboard, deduplication, hitl, transfers, audits)
|   |   |-- components/          # Shared components (TopNav, tables, badges, modals)
|   |   `-- lib/                 # Utilities (RFC 4180 CSV export, API client)
|   `-- README.md                # Frontend architecture and UI guide
|
|-- data/                        # Datasets, evaluation benchmarks, and sample documents
|   |-- evaluation/              # 150-case Golden Benchmark suite and automated evaluator
|   |-- scanned_images/          # Real scanned procurement documents (MTCs and Challans)
|   |-- taxonomies/              # UNSPSC v26 and Government e-Marketplace (GeM) cross-walks
|   `-- README.md                # Data directory overview and catalog formats
|
|-- tests/                       # Complete automated Pytest test suite (82 test cases)
|   |-- test_active_learning.py  # Active learning feedback and dialect thesaurus tests
|   |-- test_api.py              # FastAPI endpoint integration tests
|   |-- test_asme_rules.py       # ASME B16.5 and ASTM metallurgy validation tests
|   |-- test_audit.py            # Audit ledger persistence and hashing tests
|   |-- test_graph_queries.py    # Neo4j query and graph link verification tests
|   |-- test_ingestion.py        # OCR parsing and tabular data extraction tests
|   |-- test_logistics.py        # Haversine distance and CISF gate pass tests
|   |-- test_ml_extraction.py    # NER tagger attribute extraction tests
|   |-- test_piping_spec_rules.py# Pipe schedules, NACE sour service, and large flange tests
|   |-- test_rotating_rules.py   # Electric motors, seals, and bearing clearance tests
|   |-- test_storage.py          # Database session and audit model tests
|   `-- README.md                # Testing strategy and execution guide
|
|-- pyproject.toml               # Python project dependencies managed via uv
|-- docker-compose.yml           # Multi-container orchestration (PostgreSQL, Neo4j, Qdrant)
`-- README.md                    # This root documentation file
```

---

## 4. Getting Started

### Prerequisites
- Python 3.12 or newer (Python 3.14 recommended). Install `uv` for fast package management:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- Node.js 18 or newer (LTS recommended) with npm.
- Git.

### Backend Setup
1. Open a terminal in the project root:
   ```powershell
   cd C:\Users\mayan\Development\Hackathons\Samanvay-AI
   ```
2. Install Python dependencies:
   ```powershell
   uv sync
   ```
3. Start the FastAPI development server:
   ```powershell
   uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Access the interactive Swagger API documentation:
   `http://localhost:8000/docs`

### Frontend Setup
1. In a separate terminal window, navigate to the `frontend/` directory:
   ```powershell
   cd C:\Users\mayan\Development\Hackathons\Samanvay-AI\frontend
   ```
2. Install dependencies:
   ```powershell
   npm install
   ```
3. Start the Next.js development server:
   ```powershell
   npm run dev
   ```
4. Access the web interface in your browser:
   `http://localhost:3000`

---

## 5. Verification and Testing

### Running Unit and Integration Tests
To execute all 82 test cases across 11 test modules:
```powershell
uv run pytest
```
All tests should pass with zero failures.

### Running the Golden Benchmark
The Golden Benchmark evaluates 150 edge cases (50 identical items, 50 safe upgrades, and 50 fatal safety traps):
```powershell
uv run python data/evaluation/run_benchmark.py
```
Expected output:
- Total Test Cases: 150
- Overall Classification Accuracy: 100.00%
- Tier-3 False Positives: 0 (must strictly be zero)
- ASME Safety Precision: 100.00%
- Average Evaluation Latency: under 0.30 ms per item

### Building the Frontend for Production
To verify TypeScript definitions and compile all static routes:
```powershell
cd frontend
npm run build
```
All 9 application routes should build cleanly without type or lint errors.

---

## 6. Key Engineering Principles for New Developers

### 1. Deterministic Safety vs. Machine Learning Hallucinations
Machine learning models are probabilistic; they cannot be trusted with life-critical engineering decisions. A 98% accurate model still carries a 2% risk of recommending a flange or valve that ruptures under refinery pressures.
- In Samanvay-AI, Machine Learning and Vector Search are used strictly for initial candidate retrieval.
- Final compatibility determination is 100% deterministic, governed by code in `tolerance.py` and `asme_rules.py`. Every rule directly implements ASME, ASTM, API, or IBR specifications.

### 2. The Three-Tier Equivalence Hierarchy
Every item comparison produces an evaluation assigned to one of three tiers:
- Tier-1 (Identical): Exact specification match across Nominal Bore, Pressure Rating, ASTM Metallurgy, and Facing End. Safe for direct drop-in replacement.
- Tier-2 (Substitute / Upgrade): Safe functional upgrade meeting or exceeding requirements (e.g., using a Class 600 valve on a Class 300 line, or Stainless Steel F316 in place of Carbon Steel A105). Automatically routed to the Human-in-the-Loop triage queue.
- Tier-3 (Incompatible): Hard safety rejection (e.g., pressure rating too low, nominal bore mismatch, downgrading stainless to carbon steel, non-IBR certified item in steam service). Prevented from substitution.

### 3. Active Learning Without Model Retraining
Enterprise retraining cycles are slow and costly. When an engineer approves or rejects a match in the HITL queue, Samanvay-AI updates an in-memory dual index in `active_learning.py`. Subsequent identical queries immediately reflect that decision in real-time (< 1ms), boosting approved matches to Rank #1 and demoting rejected traps.

### 4. Native Hardware-Accelerated OCR
For Mill Test Certificate extraction, `ocr_engine.py` prioritizes native Windows Media OCR (`winocr`) on Windows environments, delivering full-page text extraction in under 250ms without external GPU requirements. On Linux platforms, it falls back seamlessly to PaddleOCR.

---

## 7. Subfolder Documentation Index

For detailed implementation notes, refer to the individual documentation files:
- [Backend Documentation](backend/README.md)
- [Application Layer](backend/app/README.md)
- [API Router & Dependency Injection](backend/app/api/README.md)
- [API v1 Route Reference](backend/app/api/v1/README.md)
- [Pydantic Contracts & Data Models](backend/app/contracts/README.md)
- [Neo4j Graph Ontology](backend/app/graph/README.md)
- [Ingestion & Document Parsing](backend/app/ingestion/README.md)
- [Data Pipeline & Catalog Loaders](backend/app/ingestion/data_pipeline/README.md)
- [Deterministic Matching & ASME Rules](backend/app/matching/README.md)
- [Machine Learning & Dialect Thesaurus](backend/app/ml/README.md)
- [Model Weights & Checkpoints](backend/app/ml/model_weights/README.md)
- [Frontend Web Portal Guide](frontend/README.md)
- [Datasets & Catalogs](data/README.md)
- [Golden Benchmark Suite](data/evaluation/README.md)
- [Pytest Test Suite Reference](tests/README.md)
