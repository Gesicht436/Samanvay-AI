# Running Samanvay AI Locally — Developer & Contributor Guide

> **Project Overview**: Samanvay AI is a sovereign, enterprise-grade AI-powered material harmonization and inter-CPSE spare parts interoperability platform designed for India's Ministry of Petroleum and Natural Gas (MoPNG). It integrates **FastAPI**, **Next.js 16**, **PostgreSQL 16**, **Qdrant Vector Engine**, and **Neo4j Graph Database**.

This guide outlines everything you need to run, test, and contribute to the platform locally on Windows, macOS, or Linux.

---

## 1. System Prerequisites

Ensure the following tools are installed on your workstation:

| Prerequisite | Recommended Version | Verification Command | Installation Link |
| :--- | :--- | :--- | :--- |
| **Docker Desktop** | 24.0+ (Engine running) | `docker --version` | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **Python** | 3.12.x | `python --version` | [python.org](https://www.python.org/downloads/) |
| **uv Package Manager** | Latest (`>= 0.5.0`) | `uv --version` | `curl -LsSf https://astral.sh/uv/install.ps1 \| iex` (Windows)<br>`curl -LsSf https://astral.sh/uv/install.sh \| sh` (Linux/macOS) |
| **Node.js & npm** | Node 20+ / 22 LTS | `node -v` && `npm -v` | [nodejs.org](https://nodejs.org/) |
| **Git** | 2.40+ | `git --version` | [git-scm.com](https://git-scm.com/) |

> [!IMPORTANT]
> **Windows Users**: Open **Docker Desktop** and verify that the status in the bottom-left corner indicates **"Engine running"** before executing Docker commands.

---

## 2. Quick Start: Choose Your Run Mode

We provide three distinct workflows depending on your objective:
- [**Method 1: Full Docker Stack (Recommended)**](#method-1-full-docker-compose-recommended) — Starts all databases, backend, and frontend in pre-configured production containers with 1 command.
- [**Method 2: Hybrid Local Dev Mode**](#method-2-hybrid-local-development-hot-reloading) — Runs databases in Docker while running FastAPI and Next.js directly on your host with instant hot-reloading.
- [**Method 3: Offline / Isolated Test Mode**](#method-3-offline--isolated-test-mode-no-docker) — Runs the full 393+ automated pytest suite using in-memory SQLite (no Docker needed).

---

## Method 1: Full Docker Compose (Recommended)

This method starts all 5 microservices in isolated, health-checked containers.

### Step 1: Clone and Navigate to the Repository
```powershell
git clone -b Hariom_Chandra https://github.com/Gesicht436/Samanvay-AI.git
cd Samanvay-AI
```

### Step 2: Build and Start the Entire Stack
```powershell
docker compose -f docker/docker-compose.yml --env-file docker/.env.docker up -d --build
```

### Step 3: Verify Container Health
```powershell
docker compose -f docker/docker-compose.yml ps
```
You should observe 5 healthy containers:
- `samanvay-ai-postgres` (Port `5432`)
- `samanvay-ai-qdrant` (Ports `6333`, `6334`)
- `samanvay-ai-neo4j` (Ports `7474`, `7687`)
- `samanvay-ai-backend` (Port `8000`)
- `samanvay-ai-frontend` (Port `3000`)

> [!NOTE]
> Upon initial startup, the backend automatically executes database migrations and seeds **5,000 authentic CPSE inventory items** from `datasets/inventory_catalog.csv` into PostgreSQL.

### Step 4: Index the Canonical Material Master (First Run Only)
To encode the 6,000+ national canonical items into the Qdrant vector database for semantic search:
```powershell
uv run python scripts/index_canonical_master.py
```

---

## Method 2: Hybrid Local Development (Hot-Reloading)

Ideal for active feature development, debugging, and modifying frontend UI or backend endpoints.

### Step 1: Start Only the Database Engines in Docker
```powershell
docker compose -f docker/docker-compose.yml --env-file docker/.env.docker up -d postgres qdrant neo4j
```

### Step 2: Set Up the Backend Environment
Open a terminal in the project root:
```powershell
# 1. Sync dependencies into virtual environment (.venv)
uv sync

# 2. Start the FastAPI development server with hot-reload
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend will automatically connect to `localhost:5432`, `localhost:6333`, and `localhost:7687` using defaults configured in `backend/app/core/config.py`.

### Step 3: Set Up and Start the Frontend
Open a second terminal window:
```powershell
cd frontend

# 1. Install frontend dependencies
npm install

# 2. Point Next.js rewrites to the local backend port
$env:INTERNAL_BACKEND_URL="http://localhost:8000"

# 3. Start Next.js development server
npm run dev
```

---

## Method 3: Offline / Isolated Test Mode (No Docker)

You can run the complete quality assurance suite without starting Docker. The test harness automatically switches to in-memory SQLite and mock vector searchers:

```powershell
# Run the entire test suite (393+ automated tests)
uv run pytest tests/

# Run tests with short traceback on failures
uv run pytest tests/ --tb=short

# Run specific functional test suites
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/ml/
uv run pytest tests/api/
```

---

## 3. Service Access & Dashboard URLs

Once the stack is running, access the services via your web browser:

| Application / Service | URL | Default Credentials / Purpose |
| :--- | :--- | :--- |
| **Web Portal (Frontend)** | [http://localhost:3000](http://localhost:3000) | Main CPSE Interoperability Platform |
| **Interactive API Docs (Swagger UI)** | [http://localhost:8000/docs](http://localhost:8000/docs) | OpenAPI interactive documentation |
| **Alternative API Docs (ReDoc)** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Clean API schema reference |
| **Backend Liveness Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | `{"status": "healthy"}` probe |
| **Neo4j Graph Browser** | [http://localhost:7474](http://localhost:7474) | User: `neo4j`<br>Password: `samanvay_graph` |
| **Qdrant Vector Dashboard** | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) | Graphical collection viewer & query console |

---

## 4. Pre-Provisioned CPSE Demo Credentials

The database auto-seeds test accounts for simulated cross-CPSE procurement:

| Role / Entity | Username | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Oil India Limited** | `OIL_OFFICER` | `oil_secure` | Duliajan, Moran, Digboi, Jodhpur depots |
| **Indian Oil Corporation** | `IOCL_OFFICER` | `iocl_secure` | Panipat, Mathura, Paradip, Guwahati refineries |
| **Oil & Natural Gas Corp** | `ONGC_OFFICER` | `ongc_secure` | Hazira, Uran, Ankleshwar, Mumbai Offshore bases |
| **Bharat Petroleum** | `BPCL_OFFICER` | `bpcl_secure` | Mumbai, Kochi, Bina, Numaligarh depots |
| **MoPNG Master Auditor** | `MOPNG_AUDITOR` | `mopng_secure` | Pan-India audit trail & cryptographic seal verification |

---

## 5. End-to-End System Smoke Verification

To verify that all services (relational DB, vector engine, graph topology, tolerance rules, and cryptographic ledger) are functioning harmoniously, run the live verification script:

```powershell
uv run python scripts/verify_live_api.py
```

This automated script performs:
1. **Semantic Search Probe** (`POST /api/v1/match/search`)
2. **Cryptographic Audit Hash-Chain Verification** (`POST /api/v1/audit/verify`)
3. **Cross-CPSE Inventory Discovery** (`GET /api/v1/graph/discover`)
4. **Logistics Topology Aggregation** (`GET /api/v1/graph/topology`)
5. **Golden Benchmark Validation** (`GET /api/v1/match/benchmark`)
6. **Digital Gate Pass Seal Issuance** (`POST /api/v1/requisition/create`)

---

## 6. Public Sharing: Cloudflare Quick Tunnel (Hackathon Demos)

To share your running local application with external evaluators, jury members, or remote teammates without configuring router port-forwarding or registering domains:

```powershell
.\scripts\start_public_tunnel.ps1
```
This launches an official Cloudflare Tunnel container attached to the Docker network and displays a live public URL (e.g., `https://random-subdomain.trycloudflare.com`) routing directly to your local frontend and backend.

---

## 7. Teardown & Clean Up

### Stop All Containers
```powershell
docker compose -f docker/docker-compose.yml down
```

### Reset All Data Volumes (Clean Slate)
If you wish to clear all databases and re-trigger auto-seeding on the next startup:
```powershell
docker compose -f docker/docker-compose.yml down -v
```

---

## 8. Troubleshooting & Common Gotchas

### 1. `failed to connect to the docker API at npipe:////./pipe/docker_engine`
- **Cause**: Docker Desktop is not running.
- **Solution**: Open Docker Desktop from the Start menu and wait until the status displays "Engine running".

### 2. `Bind for 0.0.0.0:5432 failed: port is already allocated`
- **Cause**: A local PostgreSQL service is already installed and running on your host machine.
- **Solution**: Stop your local PostgreSQL service:
  ```powershell
  # Windows PowerShell (Run as Administrator)
  Stop-Service postgresql*
  ```

### 3. `Vector search is unavailable because the Qdrant client is not configured`
- **Cause**: The Qdrant vector index has not been seeded yet.
- **Solution**: Run `uv run python scripts/index_canonical_master.py` to populate the `canonical_materials` vector collection.

### 4. `Frontend API calls return Network Error / 502 Bad Gateway`
- **Cause**: When running the frontend locally in Hybrid Mode (outside Docker), Next.js cannot find `http://samanvay-ai-backend:8000`.
- **Solution**: Ensure `$env:INTERNAL_BACKEND_URL="http://localhost:8000"` is set in the terminal before running `npm run dev`.
