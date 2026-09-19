# Samanvay-AI Sovereign Docker Architecture

**Project Name:** `Samanvay-AI`  
**Version:** `2.0.0-PROD`  
**Organization:** Ministry of Petroleum & Natural Gas (MoPNG) / BharatCodex  
**Target Milestone:** 100% Private, Sovereign Air-Gapped Deployment  

---

## 1. Personalized Container & Image Matrix

All services, containers, network interfaces, and volume mounts are explicitly named and branded for `Samanvay-AI`:

| Service | Container Name | Image Name & Tag | Port Bindings | Role & Responsibilities |
|---|---|---|---|---|
| **PostgreSQL 16** | `samanvay-ai-postgres` | `samanvay-ai/postgres:16-alpine` | `5432:5432` | Relational master ledger, active requisitions, inventory locks, cryptographic SHA-256 audit ledger. |
| **Qdrant** | `samanvay-ai-qdrant` | `samanvay-ai/qdrant:v1.12.0` | `6333:6333`, `6334:6334` | Vector database with 1024-dim HNSW Cosine indexing for `BAAI/bge-m3` embeddings. |
| **Neo4j 5.20** | `samanvay-ai-neo4j` | `samanvay-ai/neo4j:5.20` | `7474:7474`, `7687:7687` | Property star knowledge graph for CPSE catalog normalization and transit topology. |
| **Backend API** | `samanvay-ai-backend` | `samanvay-ai/backend:2.0.0-PROD` | `8000:8000` | FastAPI REST gateway, DeBERTa-v3 NER, deterministic 21-rule engineering safety core. |
| **Frontend UI** | `samanvay-ai-frontend` | `samanvay-ai/frontend:2.0.0-PROD` | `3000:3000` | Next.js 16.3.5 (Turbopack) industrial web portal, executive command center, split-screen MTC review. |

---

## 2. Quick Start Commands

### A. Launch All Services (Sovereign Air-Gapped Stack)
```bash
# From repository root:
docker compose up -d

# Or explicitly targeting the docker directory:
docker compose -f docker/docker-compose.yml up -d
```

### B. View Running Samanvay-AI Containers
```bash
docker ps --filter "name=samanvay-ai"
```

### C. Check Logs
```bash
# Tail logs for all Samanvay-AI services:
docker compose logs -f

# Tail backend service logs:
docker logs -f samanvay-ai-backend

# Tail frontend service logs:
docker logs -f samanvay-ai-frontend
```

### D. Tear Down & Clean Volumes
```bash
# Stop containers without removing persistent data:
docker compose down

# Stop and purge persistent data volumes:
docker compose down -v
```

---

## 3. Sovereign Air-Gapped Guarantees

1. **Zero External Cloud Calls:** Runs entirely local inference using ONNX Runtime, HuggingFace local models, and local PostgreSQL/Neo4j/Qdrant.
2. **Hardened Non-Root Users:** Backend (`samanvay:10001`) and frontend (`nextjs:1001`) run as unprivileged non-root users.
3. **Automated Healthchecks:** Every container has native healthchecks; the frontend waits for the backend, and the backend waits for PostgreSQL, Qdrant, and Neo4j to be completely healthy before accepting traffic.
