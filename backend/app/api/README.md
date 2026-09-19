# API Layer & Dependencies (`backend/app/api/`)

This directory defines the HTTP controllers, route registries, and dependency injection providers for the **Samanvay-AI** API.

---

## 1. File-by-File Breakdown

### `dependencies.py` — FastAPI Dependency Injection Providers
- **Purpose:** Houses reusable dependencies injected into router endpoints via `Depends()`.
- **Key Functions & Classes:**
  - `validate_idempotency_key(request: Request, x_idempotency_key: Optional[str] = Header(None)) -> str`:
    - Enforces idempotency on state-mutating requests (e.g. `POST /requisitions`).
    - Verifies that network retries or double clicks do not create duplicate requisitions or double-lock warehouse inventory.
  - `verify_cpse_access(request: Request, x_cpse: str = Header(default="IOCL", alias="X-CPSE-ID")) -> str`:
    - Enforces multi-tenant CPSE identity.
    - Validates that the requesting enterprise belongs to the recognized sovereign list (`IOCL`, `ONGC`, `GAIL`, `BPCL`, `HPCL`).
  - `PaginationParams`:
    - Standardized query parameter model (`page: int = 1`, `page_size: int = 20`).
    - Enforces upper bounds (`page_size <= 100`) to prevent denial-of-service memory exhaustion.

### `routers/` — Endpoint Sub-routers
Contains sub-routers for matching, requisitions, inventory, graph, sovereign audit, and document ingestion.

---

## 2. Code Example

```python
from fastapi import APIRouter, Depends
from backend.app.api.dependencies import verify_cpse_access, PaginationParams

router = APIRouter()

@router.get("/my-endpoint")
def sample_handler(
    cpse: str = Depends(verify_cpse_access),
    pagination: PaginationParams = Depends()
):
    return {"enterprise": cpse, "page": pagination.page}
```
