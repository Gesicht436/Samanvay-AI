# Backend Application Layer (`backend/`)

## 1. Architectural Role & Overview

The `backend/` directory serves as the root gateway and orchestrator of the **Samanvay-AI** application server.

Built with **FastAPI**, **SQLAlchemy 2.0**, and **Pydantic v2**, it exposes high-throughput, asynchronous REST endpoints for cross-CPSE spare parts discovery, material test certificate processing, automated safety rule compliance, sovereign cryptographic auditing, and real-time graph synchronization.

```mermaid
flowchart TD
    Client["Client Applications (React Frontend / Public API)"] --> Gateway["backend/main.py: FastAPI Application Gateway"]

    subgraph LifespanLifecycle["Application Lifespan Events"]
        InitDB["1. init_db(): Schema & DDL Verification"]
        AutoSeed["2. seeder.py: Auto-Seed 5k Catalog & 23 Users"]
        SeedAL["3. active_learning.py: Pre-seed Golden Benchmarks"]
        StartCDC["4. cdc_manager.py: Embedded CDC Worker Thread"]
    end

    Gateway --> LifespanLifecycle

    subgraph MountedRouters["Mounted API Routers (/api/v1)"]
        Gateway --> R_Auth["/api/v1/auth (JWT RBAC)"]
        Gateway --> R_Match["/api/v1/match (Zero-Mock Match Pipeline)"]
        Gateway --> R_Inv["/api/v1/inventory (Stock & Privacy Radar)"]
        Gateway --> R_Req["/api/v1/requisition (Atomic 2-Phase Locks & Gate Passes)"]
        Gateway --> R_Ingest["/api/v1/ingest (Dual-Path OCR & MTC Chemistry)"]
        Gateway --> R_Graph["/api/v1/graph (Pre-Purchase Radar & Mesh Topology)"]
        Gateway --> R_Audit["/api/v1/audit (CVC/CAG Hash Chain Ledger)"]
        Gateway --> R_Health["GET /health (Liveness & Version Probe)"]
    end
```

---

## 2. Directory Structure

```
backend/
├── app/                  # Application core, persistence, schemas, and routers
│   ├── api/              # Dependencies, domain routers, and v1 endpoints
│   ├── contracts/        # Decoupled Data Transfer Objects (DTOs)
│   ├── core/             # Configuration, cryptographic security, and exceptions
│   ├── graph/            # Neo4j Bolt driver and Cypher query templates
│   ├── ingestion/        # Document extraction, MTC parsing, and ASTM checks
│   ├── matching/         # ASME tolerance rules and alloy upgrade DAGs
│   ├── models/           # SQLAlchemy ORM declarative table entities
│   ├── schemas/          # Pydantic v2 validation contracts and privacy firewalls
│   ├── services/         # Business logic and domain service implementations
│   ├── config.py         # Application settings provider
│   └── main.py           # Backward-compatible proxy to backend.main:app
├── main.py               # Master FastAPI application entrypoint & lifespan
└── __init__.py           # Package namespace anchor
```

---

## 3. Application Lifecycle Management (`backend/main.py`)

The application utilizes FastAPI's `@asynccontextmanager lifespan` hook to perform critical system initializations on startup and graceful teardown on exit:

1. **Relational Schema Verification**: Executes `init_db()`, confirming table existence and constraints.
2. **Deterministic Auto-Seeding**:
   - `seed_database_if_empty()`: Populates PostgreSQL with 5,000 authentic CPSE catalog items from `datasets/inventory_catalog.csv` if the table is uninitialized.
   - `seed_users_if_empty()`: Guarantees that all 23 default persona users across OIL, IOCL, ONGC, GAIL, BPCL, HPCL, NRL, and MoPNG exist with active credentials.
3. **Active Learning Cold-Start**:
   - `seed_from_golden_benchmarks()`: Loads the 150 golden benchmark cases into memory, establishing initial high-confidence decision boundaries before user interaction.
4. **Embedded Change Data Capture**:
   - Starts a background daemon thread running `start_cdc_worker()`, which listens to PostgreSQL transactional triggers on `inventory_items` and `requisitions` and immediately mirrors events to Neo4j.
   - Cleans up and stops the worker thread when the server receives a shutdown signal.

---

## 4. Middleware & Cross-Origin Resource Sharing (CORS)

Configured to support local development and multi-container Docker environments:
- Permitted Origins: `http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:3001`.
- Regex Allowance: Automatically matches local loopback and standard private enterprise subnets (`192.168.*`, `10.*`) on port 3000.
- Allowed Headers & Methods: Wildcard (`*`) with `allow_credentials=True`.

---

## 5. Running the Backend Server

```powershell
# Using uv runner (recommended)
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Using activated virtual environment
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI documentation is automatically served at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health Probe: `http://localhost:8000/health`
