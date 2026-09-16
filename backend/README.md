# Samanvay-AI Backend Service

## 1. Overview
The `backend` directory contains the FastAPI-based application that powers the core logic of Samanvay-AI:
- Deterministic ASME, ASTM, and IBR engineering compatibility validation.
- Multi-modal document ingestion and high-performance optical character recognition (OCR).
- Named Entity Recognition (NER) and CPSE refinery dialect normalization.
- High-speed vector candidate retrieval and active learning dynamic reranking.
- Cross-CPSE requisition workflows, GIS routing calculations, and CISF material gate pass generation.
- Sovereign audit logging with cryptographic SHA-256 integrity checks.

---

## 2. Directory Structure

```
backend/
|-- app/
|   |-- api/                     # API routers and dependency injection
|   |   |-- deps.py              # Database session dependencies and service injection
|   |   `-- v1/                  # REST endpoints: match, requisition, ingest, graph, audit
|   |-- contracts/               # Pydantic v2 domain models and schema definitions
|   |-- graph/                   # Neo4j graph client, Cypher queries, and graph seeding
|   |-- ingestion/               # OCR engine, PDF parsers, and SQLite/PostgreSQL storage
|   |   `-- data_pipeline/       # Catalog streaming loaders and synthetic generators
|   |-- matching/                # ASME/ASTM safety engine, logistics, and active learning
|   |-- ml/                      # NER tagger, dialect thesaurus, and vector retrieval
|   |   `-- model_weights/       # Local model checkpoints and tokenizer configs
|   |-- config.py                # Global settings loaded via pydantic-settings
|   `-- main.py                  # FastAPI application entrypoint, CORS, and lifespans
|-- README.md                    # This documentation file
```

---

## 3. Technology Stack & Dependencies
- Framework: FastAPI 0.115+ (ASGI framework with async/await support).
- Validation: Pydantic v2 (Strict type enforcement and data normalization).
- Package Manager: `uv` (Fast Python package manager by Astral).
- Persistence Layer: SQLAlchemy ORM with dual-mode SQLite (default local development) and PostgreSQL (production).
- Graph Database: Neo4j Python driver with Cypher queries and in-memory mock fallback.
- Vector Search: Qdrant Client with dense cosine similarity and fast feature-based embedding fallback.
- Document Intake: Native Windows Media OCR (`winocr`), PaddleOCR, and PDFPlumber.

---

## 4. Local Development Setup

### 1. Environment Setup with `uv`
Run from the repository root:
```powershell
uv sync
```
This command inspects `pyproject.toml`, sets up a virtual environment in `.venv`, and installs all dependencies.

### 2. Configuration Settings (`config.py`)
Configuration is managed using Pydantic Settings. Default values enable immediate local execution without requiring external database containers.

Key settings include:
- `PROJECT_NAME`: `Samanvay-AI Material Standardization Engine`
- `API_V1_STR`: `/api/v1`
- `DATABASE_URL`: Defaults to local SQLite (`sqlite:///./samanvay.db`) or PostgreSQL (`postgresql+psycopg2://postgres:postgres@localhost:5432/samanvay`).
- `NEO4J_URI`: Defaults to `bolt://localhost:7687` (gracefully falls back to mock graph when offline).
- `QDRANT_HOST` / `QDRANT_PORT`: Vector database connection settings (gracefully falls back to mock vector index when offline).

To customize values, create a `.env` file in the repository root or set environment variables in your terminal:
```powershell
$env:DATABASE_URL="sqlite:///./samanvay.db"
$env:DEBUG="True"
```

### 3. Launching the Backend Server
Run using `uv`:
```powershell
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server starts at `http://127.0.0.1:8000`.
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON Schema: `http://127.0.0.1:8000/openapi.json`
- Health Check: `http://127.0.0.1:8000/health`

---

## 5. Key Subsystems Explained

### A. Matching and Safety Tolerance (`backend/app/matching/`)
- `tolerance.py`: Orchestrates the evaluation of a candidate pool against ASME and ASTM engineering specifications.
- `asme_rules.py`: Contains deterministic pressure ladders (Class 150 through 2500) and directed acyclic graphs for metallurgy compatibility.
- `piping_spec_rules.py`: Validates pipe schedules, NACE MR0175 sour service requirements, ASME B16.47 flange series, and statutory IBR certification.
- `active_learning.py`: Dual-indexed cache storing human expert approvals and rejections to dynamically boost or demote future matching candidates.
- `logistics.py`: Computes Haversine road distances between CPSE refineries, calculates road transit lead times, manages surplus reservation locks, and issues digital CISF material gate passes.

### B. Machine Learning and Dialect Normalization (`backend/app/ml/`)
- `ner_tagger.py`: Converts messy CPSE strings (e.g., `NRV 2IN 150# CS`) into standardized attributes. Handles metric millimeter conversions, inch dimensions, and Indian refinery shorthand (`NRV`, `BFV`, `SPRF`, `LTCS`, `DSS`, `IBR`).
- `vector_search.py`: Fast semantic retrieval of the top-K canonical candidates from the master catalog before safety rules run.

### C. Ingestion and OCR (`backend/app/ingestion/`)
- `ocr_engine.py`: Multi-tier optical character recognition pipeline. Prioritizes native Windows Media OCR (`winocr`) for sub-250ms text extraction from scanned MTC images.
- `certificate.py`: Specialized tabular parser extracting heat numbers, mechanical yield strength, and chemical compositions (Carbon, Sulfur, Phosphorus, Chromium, Molybdenum).
- `storage.py`: SQLAlchemy database models for ingested documents, inventory items, and audit logging utilities.

### D. Central Inventory & Inward Lifecycle Management (`backend/app/api/v1/inventory.py`)
- Inward Procurement Bill Commit: Site engineers upload scanned bills or MTC certificates, inspect/modify parsed specifications (heat number, metallurgy, dimensions, PO number), and commit items into PostgreSQL with an initial lifecycle status.
- Lifecycle Statuses:
  - `TO_BE_CONSUMED`: Item received and reserved for scheduled turnaround or upcoming unit maintenance. Stored internally in PostgreSQL and mirrored in Neo4j with status `TO_BE_CONSUMED`; completely excluded from sister CPSE surplus radar search results.
  - `IN_STORAGE`: Standard warehouse reserve buffer stock.
  - `IDLE_SURPLUS`: Flagged when turnaround is completed or delayed without utilizing the item. Immediately broadcasted live to sister CPSEs (IOCL, ONGC, BPCL) in cross-CPSE surplus discovery queries (`find_inter_cpse_spares`).
  - `RESERVED_TRANSFER`: Reserved by an indenting sister CPSE with an active inventory lock.
  - `CONSUMED`: Installed in a refinery processing unit; quantity decremented to 0 and archived from active stock.
- REST Endpoints:
  - `POST /api/v1/inventory/commit-bill`: Commits verified procurement bill item and syncs to Neo4j.
  - `GET /api/v1/inventory/items`: Lists plant inventory items filtered by CPSE, status, or depot.
  - `GET /api/v1/inventory/{item_id}`: Retrieves single item record by primary key.
  - `PATCH /api/v1/inventory/{item_id}/status`: Transitions item status (e.g. `TO_BE_CONSUMED` -> `IDLE_SURPLUS`) and updates the Knowledge Graph in real-time.

---

## 6. Running Tests
To run all tests:
```powershell
uv run pytest
```
To run tests for a specific module:
```powershell
uv run pytest tests/test_inventory_lifecycle.py -v
```

