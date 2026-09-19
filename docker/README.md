# Samanvay-AI Sovereign Docker Infrastructure (`docker/`)

**Project Name:** `Samanvay-AI`  
**Version:** `2.0.0-PROD`  
**Organization:** Ministry of Petroleum & Natural Gas (MoPNG) / BharatCodex  
**Target Milestone:** 100% Private, Sovereign Air-Gapped Deployment  

This directory contains the production multi-container orchestration manifests, Dockerfiles, initialization scripts, and environment configurations powering **Samanvay-AI**.

---

## 1. Container & Image Architecture

The stack consists of 5 tightly integrated, healthcheck-coordinated services connected over an isolated Docker bridge network (`samanvay-network`):

```
                       ┌─────────────────────────────────────────┐
                       │   Frontend UI (samanvay-ai-frontend)    │
                       │   Next.js 16.3.5 / Turbopack (Port 3000)│
                       └────────────────────┬────────────────────┘
                                            │
                                            ▼ HTTP / REST
                       ┌─────────────────────────────────────────┐
                       │    Backend API (samanvay-ai-backend)    │
                       │    FastAPI / Python 3.11 (Port 8000)    │
                       └───────────┬──────────────┬──────────────┘
                                   │              │
                   ┌───────────────┘              └───────────────┐
                   ▼                                              ▼
     ┌───────────────────────────┐                  ┌───────────────────────────┐
     │  PostgreSQL 16 Database   │                  │   Qdrant Vector Database  │
     │  (samanvay-ai-postgres)   │                  │    (samanvay-ai-qdrant)   │
     │  Port 5432 / Persistent   │                  │    Port 6333 / HNSW Index │
     └─────────────┬─────────────┘                  └───────────────────────────┘
                   │
                   ▼ CDC Mirroring
     ┌───────────────────────────┐
     │    Neo4j 5.20 Graph DB    │
     │    (samanvay-ai-neo4j)    │
     │    Port 7474 / Port 7687  │
     └───────────────────────────┘
```

| Service | Container Name | Image Name & Tag | Port Bindings | Role & Responsibilities |
|---|---|---|---|---|
| **PostgreSQL 16** | `samanvay-ai-postgres` | `samanvay-ai/postgres:16-alpine` | `5432:5432` | Relational master ledger, active requisitions, inventory locks, cryptographic SHA-256 audit ledger. |
| **Qdrant** | `samanvay-ai-qdrant` | `samanvay-ai/qdrant:v1.12.0` | `6333:6333`, `6334:6334` | Vector database with 1024-dim HNSW Cosine indexing for `BAAI/bge-m3` embeddings. |
| **Neo4j 5.20** | `samanvay-ai-neo4j` | `samanvay-ai/neo4j:5.20` | `7474:7474`, `7687:7687` | Property star knowledge graph for CPSE catalog normalization and transit topology. |
| **Backend API** | `samanvay-ai-backend` | `samanvay-ai/backend:2.0.0-PROD` | `8000:8000` | FastAPI REST gateway, DeBERTa-v3 NER, deterministic 21-rule engineering safety core. |
| **Frontend UI** | `samanvay-ai-frontend` | `samanvay-ai/frontend:2.0.0-PROD` | `3000:3000` | Next.js 16.3.5 (Turbopack) industrial web portal, executive command center, split-screen MTC review. |

---

## 2. Directory Structure

```
docker/
├── .dockerignore             # Production build context exclusions
├── .env.docker               # Container environment variables
├── docker-compose.yml        # Multi-service stack definition
├── Dockerfile.backend        # Multi-stage hardened Python 3.11 backend container
├── Dockerfile.frontend       # Multi-stage optimized Next.js standalone container
├── init-db/                  # Database initialization hooks
│   ├── 01-init-samanvay.sql  # SQL script creating extensions and permissions
│   └── README.md             # Documentation for database init
└── README.md                 # This file
```

---

## 3. Quick Start Commands

### A. Launch All Services
```bash
# Launch stack in background
docker compose -f docker/docker-compose.yml up -d
```

### B. Verify Health & Running Containers
```bash
docker ps --filter "name=samanvay-ai"
```

### C. Tail Logs
```bash
# All services
docker compose -f docker/docker-compose.yml logs -f

# Backend only
docker logs -f samanvay-ai-backend

# Frontend only
docker logs -f samanvay-ai-frontend
```

### D. Tear Down & Purge Volumes
```bash
# Stop containers preserving data:
docker compose -f docker/docker-compose.yml down

# Stop containers and purge persistent database volumes:
docker compose -f docker/docker-compose.yml down -v
```

---

## 4. Sovereign Air-Gapped Guarantees

1. **Zero External Cloud Calls:** Runs entirely local inference using ONNX Runtime, HuggingFace local models, and local PostgreSQL/Neo4j/Qdrant.
2. **Hardened Non-Root Users:** Backend (`samanvay:10001`) and frontend (`nextjs:1001`) run as unprivileged non-root users.
3. **Automated Healthchecks:** Every container has native healthchecks; the frontend waits for the backend, and the backend waits for PostgreSQL, Qdrant, and Neo4j to be completely healthy before accepting traffic.
