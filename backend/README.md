# Samanvay-AI Backend Service (`backend/`)

The `backend/` directory houses the core RESTful microservice API powering **Samanvay-AI**.

Built with **FastAPI**, **SQLAlchemy ORM**, **Pydantic v2**, and **PostgreSQL 16**, the backend acts as the secure central gateway coordinating the Machine Learning pipeline, the Deterministic Engineering Safety Core, the Neo4j Knowledge Graph, and the Sovereign SHA-256 Audit Ledger.

---

## 1. Architectural Role & Responsibilities

```
                                [ Next.js Frontend UI ]
                                          │
                                          │ HTTP / JSON / Multipart
                                          ▼
                      ┌───────────────────────────────────────┐
                      │      FastAPI Gateway (backend/main.py)│
                      │  • CORS & Middleware                  │
                      │  • CPSE Multi-Tenant Headers          │
                      │  • Idempotency Gatekeeper             │
                      └───────────────────┬───────────────────┘
                                          │
             ┌────────────────────────────┼────────────────────────────┐
             ▼                            ▼                            ▼
       [ Routers ]                  [ Services ]                 [ Core / DB ]
    • /match (NER+Rules)       • requisition_service        • PostgreSQL (ACID)
    • /requisition (Orders)    • inventory_service          • Neo4j Graph Driver
    • /inventory (Catalog)     • audit_service (SHA-256)    • Qdrant Vector Client
    • /graph (Logistics)       • cdc_manager (Sync Worker)  • Security Primitives
    • /audit (Sovereign)       • seeder (Cold Start)
    • /ingest (Vision OCR)
```

---

## 2. Directory Structure

```
backend/
├── main.py                   # Application entry point, lifespan events, CORS, route mounting
├── app/
│   ├── api/                  # API layer
│   │   ├── dependencies.py   # Auth headers, idempotency validator, pagination params
│   │   └── routers/          # Endpoint controllers (match, req, inventory, graph, audit, ingest)
│   ├── core/                 # Configuration, exceptions, cryptographic security functions
│   ├── models/               # SQLAlchemy ORM declarative database models
│   ├── schemas/              # Pydantic v2 data validation and serialization models
│   └── services/             # Business logic, transactional processing, CDC worker
```

---

## 3. Tech Stack & Dependencies

| Component | Library / Version | Role |
|---|---|---|
| **Web Framework** | `FastAPI ^0.110.0` | High-throughput asynchronous REST API with automatic OpenAPI documentation. |
| **ASGI Server** | `Uvicorn ^0.29.0` | Production ASGI web server running with uvloop and httptools. |
| **Data Validation** | `Pydantic v2 ^2.6.0` | Strict input parsing, serialization, and schema contracts. |
| **Relational ORM** | `SQLAlchemy ^2.0.28` | Transactional data persistence, relationship mapping, row-level locking. |
| **Database Driver** | `psycopg2-binary` | PostgreSQL connection pool driver. |
| **Security & Crypto** | `hashlib`, `hmac` | SHA-256 cryptographic chain hashing and gate-pass signing. |

---

## 4. Running the Backend

### Local Development:
```bash
# Activate virtual environment
.venv\Scripts\activate

# Start API server with live reload on port 8000
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Interactive API Documentation:
Once running, open your browser:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 5. How to Run Tests

```bash
# Run all backend API endpoint tests
pytest tests/api/ -v

# Run integration tests with full database
pytest tests/integration/ -v
```
