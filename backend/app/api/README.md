# API Layer (`backend/app/api`)

## 1. Overview
The `api` package establishes the HTTP gateway for Samanvay-AI. It coordinates routing, dependency injection, input validation, and versioning.

---

## 2. Directory Structure

```
backend/app/api/
|-- v1/                          # Version 1 API routers
|   |-- audit.py                 # Sovereign audit trail and compliance ledger
|   |-- graph.py                 # Knowledge graph and taxonomy traversal
|   |-- ingest.py                # Multi-modal OCR and document ingestion
|   |-- match.py                 # Material standardization and HITL triage
|   |-- requisition.py           # Inter-CPSE transfers, GIS logistics, and gate passes
|   `-- README.md                # Detailed v1 endpoint specification
|-- deps.py                      # Common dependency injection providers
`-- README.md                    # This file
```

---

## 3. Dependency Injection (`deps.py`)

FastAPI uses dependency injection to pass shared resources into route handlers. This promotes testability, clean separation of concerns, and reliable resource teardown.

### Database Session Provider (`get_db`)
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
- Each incoming request that declares `db: Session = Depends(get_db)` receives its own dedicated database session.
- When the request completes, the `finally` block guarantees that the database connection is closed and returned to the connection pool, preventing connection leaks.

---

## 4. API Versioning Strategy

All application endpoints are versioned under the `/api/v1` prefix defined in `backend/app/config.py`:
- Modularity: Each major feature domain has its own dedicated router file inside `api/v1/`.
- Aggregation: The master router in `main.py` includes each feature router with distinct prefixes:
  - `/api/v1/match` -> Material standardization and HITL triage.
  - `/api/v1/requisition` -> Inter-CPSE transfer workflows and logistics.
  - `/api/v1/ingest` -> Multi-modal document and MTC intake.
  - `/api/v1/graph` -> Neo4j ontology exploration.
  - `/api/v1/audit` -> Sovereign compliance audit trail.

---

## 5. Standard HTTP Status Codes Used
- `200 OK`: Successful retrieval or execution.
- `201 Created`: Successful creation of a requisition, lock, or audit record.
- `400 Bad Request`: Missing or malformed parameters.
- `404 Not Found`: Requested SKU, requisition ID, or certificate not found.
- `422 Unprocessable Entity`: Schema validation error triggered automatically by Pydantic v2.
- `500 Internal Server Error`: Unhandled server exception with structured error logs.
