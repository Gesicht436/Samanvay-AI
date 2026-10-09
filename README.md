# Samanvay-AI

Samanvay-AI is a material intelligence workspace for harmonizing procurement
catalogs across Indian central public sector enterprises (CPSEs), with a focus
on IOCL, ONGC, and BPCL. It combines document extraction, engineering
attribute normalization, catalog retrieval, deterministic compatibility
checks, and human review in one web application.

This repository is a contract-first monorepo: FastAPI/Pydantic contracts define
the backend API, and the Next.js client mirrors the response types it consumes.
The core matching and engineering rules are implemented in Python, Polars, and
NumPy; this project does not require native C++ extensions.

## What the application does

- **Ingest certificates and other documents:** upload a PDF or supported image,
  or submit certificate text directly. Native PDF text is extracted without
  OCR. Scanned PDF pages and images use 300-DPI rendering, denoising, deskew,
  contrast enhancement, PaddleOCR, and EasyOCR fallback.
- **Extract material evidence:** parse certificate identifiers, purchase
  orders, grades, standards, heat numbers, chemistry, mechanical properties,
  manufacturer, TPI/inspection agency, and engineering attributes.
- **Calculate and review chemistry:** calculate IIW carbon equivalent,
  weldability category, and PREN when the required values are present. Current
  chemistry conformance ranges are configured for A105 and A182 F316. Unknown
  grades and incomplete or out-of-range chemistry are not marked verified and
  require human review.
- **Find catalog equivalents:** retrieve likely canonical materials from
  Qdrant using dimensional, metallurgy, pressure/temperature, and
  standards/procurement evidence, then apply deterministic compatibility and
  safety rules. A compatibility reranker is used when requested and available.
- **Capture human decisions:** queue uncertain match suggestions, accept or
  correct them, and expose the resulting feedback examples for future learning.
  The current feedback queue is in memory and is cleared when the API process
  restarts.

## User workflow

1. Open **Document intake** (`/ingest`) to capture a certificate, upload a
   document, or paste text.
2. The browser sends the input to the FastAPI service. Document uploads are
   sent as bytes to `POST /v1/ingest/document`; the backend returns OCR pages,
   extraction metadata, parsed fields, chemistry results, conformance warnings,
   and whether human review is required.
3. Review extracted certificate fields and page-level OCR routing/engine
   information. Unverified chemistry is flagged for human review.
4. Open **Material matching** (`/deduplication`) and enter a catalog or
   engineering description to retrieve ranked canonical candidates.
5. Review candidate attributes, compatibility tier, and safety reasons. Resolve
   uncertain suggestions in **Review queue** (`/hitl`); the queue and captured
   feedback are currently process-local.
6. Use **Dashboard** (`/dashboard`) for API-reported OCR-engine readiness,
   matching-service readiness, review counts, and available capabilities.

## Architecture and data flow

```text
Next.js browser UI
  ├── /ingest          → POST /v1/ingest/document or /v1/ingest/text
  ├── /deduplication   → POST /v1/match
  ├── /hitl            → /v1/match/hitl-queue and /v1/match/hitl-resolve
  └── /dashboard       → GET /v1/dashboard/summary
                              │
                              ▼
FastAPI routers → Pydantic contracts → application services
  ├── OCR/pipeline.py
  │     ├── native PDF text extraction per page
  │     └── 300-DPI OCR + preprocessing → PaddleOCR → EasyOCR fallback
  ├── backend/app/ingestion/
  │     ├── certificate.py parses MTC fields, chemistry, and mechanical tests
  │     ├── chemistry.py calculates CE/PREN and checks supported grade ranges
  │     └── document.py composes OCR + MTC + chemistry + review status
  └── backend/app/matching/ + machine_learning/
        ├── attribute normalization and deterministic safety/tolerance rules
        ├── Qdrant named-vector candidate retrieval
        ├── optional compatibility reranker and NER model
        └── in-memory active-learning/HITL queue
```

The OCR profile and page-level method, OCR engine, and raster DPI are part of
the document response. The backend response contracts live in
[`backend/app/contracts/`](./backend/app/contracts/); matching, ingestion, and
dashboard details are mirrored by the frontend types in
[`frontend/src/lib/types.ts`](./frontend/src/lib/types.ts).

## Repository map

| Path | Purpose |
| --- | --- |
| [`frontend/`](./frontend/) | Next.js 16 / React 19 procurement workspace |
| [`backend/app/api/v1/`](./backend/app/api/v1/) | FastAPI endpoints for ingest, matching, HITL, graph, auth, and dashboard |
| [`backend/app/contracts/`](./backend/app/contracts/) | Pydantic API and domain contracts |
| [`backend/app/ingestion/`](./backend/app/ingestion/) | MTC parsing, document orchestration, and chemistry calculations |
| [`backend/app/matching/`](./backend/app/matching/) | Deterministic tolerance and safety classifications |
| [`OCR/`](./OCR/) | OCR engines, PDF/image extraction, layout, and text normalization |
| [`machine_learning/`](./machine_learning/) | NER, vector retrieval, reranking, active learning, and training |
| [`data/`](./data/) | Source documents, catalogs, taxonomies, and training inputs |
| [`deployment/`](./deployment/) | Local Qdrant, Neo4j, and PostgreSQL compose services |
| [`tests/`](./tests/) | API, ingestion, OCR, matching, and ML tests |
| [`docs/`](./docs/) | Focused architecture, OCR, matching, ML, graph, and deployment notes |

## Requirements

- Windows, macOS, or Linux
- Python **3.11 or 3.12** (Python 3.14 is not supported)
- Node.js and npm for the frontend
- Git if you need to sync upstream catalog/training data
- Docker Desktop only if you want to run the optional compose services

## Local setup

### 1. Create and install the Python environment

From the repository root, in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

To install document OCR and the optional ML stack, install the `ml` extra as
well:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ml,dev]"
```

The `ml` extra includes PaddleOCR, PaddlePaddle, EasyOCR, Pillow, and the
optional model-training/retrieval packages. OCR installation can be large.
Without it, native-text PDF ingestion and non-ML API functionality remain
available, but scanned-document OCR and model-backed matching may not be.

To use the project bootstrap script instead, run:

```powershell
.\scripts\setup.ps1
```

It creates `.venv` if needed, installs the development extra, and runs tests.
Install `.[ml,dev]` afterward when OCR/ML capabilities are needed.

### 2. Start the backend

In a terminal at the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

The API runs at `http://localhost:8000`. Interactive OpenAPI documentation is
at `http://localhost:8000/docs`; health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

### 3. Start the frontend

In another terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://localhost:3000`. By default the browser client calls the API on
port 8000 using the current hostname. To use another API host, create
`frontend/.env.local`:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Restart the frontend after changing the environment file.

## Optional data, models, and infrastructure

### Data

Catalogs, taxonomies, example documents, and training inputs live under
[`data/`](./data/). Data is source input; application commands should not
regenerate `data/ml_training/` or `data/mock_cpes_catalogs/`. If the upstream
Samanvay-AI data is needed, sync it on Windows with:

```powershell
.\scripts\sync-upstream-data.ps1
```

The script downloads/copies the upstream data from the project repository;
review its behavior before running it in a restricted environment.

### Catalog matching

Matching requires the canonical catalog, a configured embedding model, and an
available Qdrant index. Model weights are not automatically downloaded by this
application. Follow the procedure in
[`docs/deployment.md`](./docs/deployment.md) and
[`docs/ml.md`](./docs/ml.md) to obtain the configured `BAAI/bge-m3` model,
configure `MODEL_WEIGHTS_PATH` if needed, and index
`data/taxonomies/canonical_master.csv`.

The index command is:

```powershell
.\.venv\Scripts\python.exe -m scripts.index_canonical_master
```

Without a ready model/index, matching reports service unavailability rather
than returning fabricated catalog results. The dashboard reports the live
matching readiness.

### Local infrastructure

Qdrant, Neo4j, and PostgreSQL can be started with Docker Compose:

```powershell
docker compose -f deployment/docker-compose.yml up -d
```

Default local settings are defined in
[`backend/app/config.py`](./backend/app/config.py): Qdrant uses
`localhost:6333` (with embedded local storage as a fallback), Neo4j uses
`bolt://localhost:7687`, and PostgreSQL uses `localhost:5432`. Override
settings through environment variables or a root `.env` file. The compose
credentials are development defaults only; do not use them in production.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | API liveness |
| `POST` | `/v1/ingest/document` | Upload a PDF or supported image (maximum 15 MB) |
| `POST` | `/v1/ingest/text` | Parse pasted certificate text |
| `POST` | `/v1/match` | Retrieve and classify material candidates |
| `GET` | `/v1/match/hitl-queue` | List pending match-review items |
| `POST` | `/v1/match/hitl-resolve` | Accept/reject or correct a review item |
| `GET` | `/v1/match/hitl-training-examples` | Read captured review examples |
| `POST` | `/v1/match/hitl-bootstrap` | Seed review examples |
| `GET` | `/v1/dashboard/summary` | Read service readiness and capabilities |
| `GET` | `/v1/graph/spare-locator` | Spare locator route |
| `GET` | `/v1/graph/visualize` | Graph visualization route |
| `GET` | `/v1/auth/me` | Current-user route |

### Example: ingest a document from PowerShell

```powershell
curl.exe -X POST "http://localhost:8000/v1/ingest/document" `
  -F "file=@data/raw/sample_mtc_flange_01.pdf"
```

The response includes OCR `pages`, `parsed_metadata`, an optional structured
`mtc` record, `chemistry`, `astm_conformance`, `ocr_profile`, confidence, and
`requires_hitl`. See the schema in
[`backend/app/contracts/ingestion.py`](./backend/app/contracts/ingestion.py).

### Example: request a material match

```powershell
curl.exe -X POST "http://localhost:8000/v1/match" `
  -H "Content-Type: application/json" `
  -d '{"raw_description":"Gate valve DN100 PN16 ASTM A216 WCB API 600","top_k":5,"rerank":true}'
```

Match output includes ranked candidates, engineering attributes, domain scores,
reasons, and a safety/tolerance tier. Unsafe or under-specified matches should
be reviewed rather than treated as automatic equivalencies.

## Development and validation

Run the complete Python test suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run focused ingestion tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_document_ingest.py tests\test_ingest_api.py tests\test_ingestion.py tests\test_mtc_chemistry.py -q
```

Run Ruff on Python files:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
```

Build/type-check the frontend:

```powershell
Set-Location frontend
npm run build
```

## Current scope and operational notes

- MTC chemistry conformance currently has configured chemistry ranges for
  **A105** and **A182 F316**. Unsupported grades, missing required chemistry,
  or out-of-range values return warnings and set `requires_hitl`; they are not
  silently declared conforming.
- The active-learning review queue is in memory. Persist feedback in an
  application database before relying on it across API restarts.
- The graph routes are present, but the current route implementations return
  placeholder node/item arrays; treat graph visualization and spare-locator
  results as scaffolding until connected to populated graph/inventory data.
- The frontend requires the backend for live ingestion, matching, and status.
  An unavailable API is reported as an error rather than implying a live result.
- See [`docs/architecture.md`](./docs/architecture.md),
  [`docs/ocr.md`](./docs/ocr.md), [`docs/ingestion.md`](./docs/ingestion.md),
  [`docs/matching.md`](./docs/matching.md), [`docs/ml.md`](./docs/ml.md),
  [`docs/graph.md`](./docs/graph.md), and
  [`docs/deployment.md`](./docs/deployment.md) for deeper implementation notes.
