# Samanvay-AI Production Deployment Guide

## 1. Architecture Overview

Samanvay-AI is packaged as a multi-container full-stack application orchestrated via Docker Compose and unified through an Nginx reverse proxy.

```
                           HACKATHON JUDGES / USERS
                                      |
                         (HTTPS via Cloudflare / ngrok)
                                      |
                                      v
                        [Nginx Edge Reverse Proxy: Port 80]
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
[/ routes: Frontend UI]                                 [/api/* & /docs: Backend]
[Next.js 15 Standalone]                                 [FastAPI Python Backend]
   (Port 3000 Internal)                                    (Port 8000 Internal)
                                                                   |
                               +-----------------------------------+-----------------------------------+
                               |                                   |                                   |
                               v                                   v                                   v
                    [PostgreSQL 16: Port 5432]         [Qdrant Vector: Port 6333]          [Neo4j Graph: Port 7687]
                    Relational Audit & Storage         2,200 Canonical Vector Master       Taxonomy & Depot Graph
```

---

## 2. Option A: Full-Stack Docker Deployment (Local Appliance)

### Prerequisites
- Docker Engine 24+ with Docker Compose v2.
- (Optional for GPU) NVIDIA Container Toolkit (`nvidia-ctk`) for CUDA hardware acceleration on RTX 3060.

### Step 1: Standard Multi-Container Launch (CPU / Universal)
To build and start all 6 services (Nginx, Frontend, Backend, Postgres, Qdrant, Neo4j):

```powershell
docker compose up -d --build
```

### Step 2: GPU-Accelerated Launch (NVIDIA CUDA)
If you have the NVIDIA Container Toolkit installed and want PyTorch to leverage your RTX 3060 GPU:

```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

### Step 3: Verify Running Services
```powershell
docker compose ps
```

All 6 services will be operational:
- Web Portal: `http://localhost` (via Nginx port 80)
- Interactive API Docs: `http://localhost/docs`
- Direct Backend: `http://localhost:8000`
- Neo4j Browser: `http://localhost:7474`
- Qdrant REST: `http://localhost:6333/dashboard`

---

## 3. Option B: Exposing Live HTTPS to Judges (Zero Cloud Cost)

To allow Smart India Hackathon judges to test the live application on their laptops/phones without hosting fees, expose your local Docker Nginx port (port 80) via a secure tunnel.

### Method 1: Cloudflare Tunnel (Recommended - Fast & Free)

1. Download `cloudflared` for Windows:
   ```powershell
   winget install --id Cloudflare.cloudflared
   ```
2. Start an instant, zero-login HTTPS tunnel pointing to port 80:
   ```powershell
   cloudflared tunnel --url http://localhost:80
   ```
3. Cloudflare outputs a public URL like:
   `https://random-words-1234.trycloudflare.com`
4. Provide this HTTPS URL to judges. Both the Next.js UI and all `/api/*` endpoints will be accessible globally.

### Method 2: ngrok Tunnel

1. If using ngrok:
   ```powershell
   ngrok http 80
   ```
2. ngrok will output:
   `Forwarding https://your-subdomain.ngrok-free.app -> http://localhost:80`

---

## 4. Option C: Direct Native Execution (Fast Development)

If you prefer running the processes directly in Windows terminal windows without Docker:

### Terminal 1: Supporting Databases (Postgres, Qdrant, Neo4j)
```powershell
docker compose up -d postgres qdrant neo4j
```

### Terminal 2: FastAPI Backend
```powershell
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 3: Next.js Frontend
```powershell
cd frontend
npm run dev
```

---

## 5. Environment Variables & Ports

| Service | Container Name | Host Port | Internal Port | Key Configuration |
|---|---|---|---|---|
| Nginx | `samanvay-nginx` | `80` | `80` | Reverse proxy routes `/api/` to backend and `/` to frontend |
| Frontend | `samanvay-frontend` | `3000` | `3000` | Next.js 15 Standalone (`NEXT_PUBLIC_API_URL=/api/v1`) |
| Backend | `samanvay-backend` | `8000` | `8000` | FastAPI Uvicorn ASGI Server |
| PostgreSQL | `samanvay-postgres` | `5432` | `5432` | User: `postgres`, DB: `samanvay_db` |
| Qdrant | `samanvay-qdrant` | `6333`, `6334` | `6333` | Collection: `canonical_materials` (1024-d) |
| Neo4j | `samanvay-neo4j` | `7474`, `7687` | `7687` | Bolt URI: `bolt://localhost:7687` |

---

## 6. Maintenance Commands

- View live container logs:
  ```powershell
  docker compose logs -f backend
  ```
- Stop all containers:
  ```powershell
  docker compose down
  ```
- Reset database volumes:
  ```powershell
  docker compose down -v
  ```
