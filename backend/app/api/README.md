# API Layer & Dependencies (`backend/app/api/`)

The `backend/app/api/` directory implements the HTTP presentation layer for **Samanvay-AI**. It handles incoming HTTP requests, resolves server-side session cookies, enforces Role-Based Access Control (RBAC) and CSRF protection, guarantees request idempotency, and routes execution to domain services.

All endpoints are mounted under the prefix `/api/v1` and are fronted in production by the **Next.js 16 standalone reverse proxy** running on port `3000` (rewriting `/api/v1/*` to FastAPI port `8000`).

---

## 1. Request Lifecycle & Dependency Pipeline

Every incoming request passes through an automated pipeline managed by FastAPI dependencies defined in [`dependencies.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/dependencies.py):

```mermaid
flowchart TD
    Req["Incoming HTTP Request<br/>(from Next.js 16 Proxy)"] --> CheckCookie{"Session Cookie Present?<br/>(HttpOnly)"}

    CheckCookie -- Yes --> ResolveSession["Resolve Server-Side Session<br/>(SHA-256 hash lookup)"]
    CheckCookie -- No --> AuthCheck{"Auth Mandatory for Endpoint?"}

    ResolveSession -- Invalid / Expired / Revoked --> Err401["HTTP 401 Unauthorized<br/>(dead cookie cleared)"]
    ResolveSession -- Live --> QueryUser["Query User in DB<br/>(Check is_active & is_approved)"]

    QueryUser -- Inactive / Unapproved --> Err401
    QueryUser -- OK --> SetUser["Inject current_user: User"]

    AuthCheck -- Public (e.g. /auth/login) --> RouteHandler
    AuthCheck -- Required --> Err401

    SetUser --> CsrfGate{"Unsafe Method?<br/>(require_csrf: Origin + X-CSRF-Token)"}
    CsrfGate -- Origin / Token Mismatch --> Err403csrf["HTTP 403 Forbidden<br/>(CSRF_ORIGIN_DENIED / CSRF_TOKEN_DENIED)"]
    CsrfGate -- Pass / Safe Method --> RoleGuard{"Permission Check<br/>(require_permission / require_roles)"}

    RoleGuard -- Denied --> ErrRole403["HTTP 403 Forbidden<br/>(AUTHORIZATION_DENIED)"]
    RoleGuard -- Allowed --> IdemCheck{"Idempotency-Key Header Present?<br/>(validate_idempotency_key)"}

    IdemCheck -- Cache Hit & Unexpired --> ReturnCache["Return Cached 200 OK<br/>(Zero Duplicate Mutation)"]
    IdemCheck -- Cache Miss / New Key --> RouteHandler["Execute Target Router Handler<br/>(e.g. /requisition, /match)"]

    RouteHandler --> DBCommit["Commit Transaction & Seal Audit Hash"]
    DBCommit --> Resp["Return HTTP Response (JSON / SVG)"]
```

---

## 2. Dependency Providers (`dependencies.py`)

The file [`dependencies.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/dependencies.py) exports production dependency functions injected via FastAPI's `Depends()`:

### A. Database Session Injection
```python
async def get_db_session() -> Generator[Session, None, None]
```
- **Description:** Contextual generator acquiring a scoped connection from `SessionLocal()` (SQLAlchemy 2.0 connection pool: 10 connections, max overflow 20).
- **Guarantees:** Automatic cleanup via `finally: db.close()`, preventing connection leakage under load.

### B. Session Authentication & Identity Extraction
```python
def get_current_session(
    request: Request,
    db: Session = Depends(get_db_session),
) -> AuthSession
```
- **Description:** Resolves the HttpOnly session cookie (`samanvay_session` in development, `__Host-samanvay_session` in production) to a live server-side [`AuthSession`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/models/tables.py) row.
- **Validation Steps:**
  1. Missing cookie → `HTTP 401` with nothing to clear.
  2. Malformed, unknown, expired, or revoked presented secret → `HTTP 401` with the dead cookie cleared and sanitized telemetry recorded.
  3. SHA-256 hash lookup only; there is no `Authorization`/Bearer fallback of any kind.

```python
def get_current_user(
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db_session),
) -> User
```
- **Description:** Loads the [`User`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/models/tables.py#L249-L270) bound to the session, enforces `is_active` and `is_approved` on every request (`HTTP 401` otherwise), and refreshes the session's `last_seen_at`.

No optional-authentication helper is exported: endpoints are either explicitly public (no auth dependency, e.g. `POST /auth/login`) or require a live session.

### C. Permission, CSRF & Role Guards
```python
def require_permission(permission: str, resource_type: Optional[str] = None)
```
- **Description:** Canonical AUTH-007 authorization dependency. Evaluates the centralized permission policy for the authenticated user; fails closed with `HTTP 403` (`{"error": "AUTHORIZATION_DENIED", ...}`) and records sanitized authorization-failure telemetry.

```python
def require_roles(allowed_roles: List[str])
```
- **Description:** Legacy role-list compatibility guard retained for routes not yet migrated to `require_permission`. Rejects roles outside the supplied list with `HTTP 403` (`Insufficient role permissions`).

```python
def require_csrf(
    request: Request,
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db_session),
) -> AuthSession
```
- **Description:** CSRF gate for unsafe methods. Validates the `Origin` header against the configured allowlist first (`HTTP 403` `{"error": "CSRF_ORIGIN_DENIED"}`), then verifies the `X-CSRF-Token` header against the session-bound synchronizer token in constant time (`HTTP 403` `{"error": "CSRF_TOKEN_DENIED"}`). Returns `HTTP 401` when no live session cookie is presented.

### D. Idempotency Key Gatekeeper
```python
def validate_idempotency_key(
    request: Request,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db_session),
)
```
- **Description:** Prevents duplicate state mutations, double inventory debits, or duplicate requisitions caused by network retries or double-clicks.
- **Mechanism:**
  - Inspects the `Idempotency-Key` HTTP header.
  - Queries [`IdempotencyKey`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/models/tables.py#L220-L231) table in PostgreSQL.
  - If a cached response exists within the 24-hour TTL, returns `{"status": "CACHED", "data": key_record.response_body}` immediately.
  - Otherwise, passes the raw key string to the service layer for transaction registration.

### E. Multi-Tenant Enterprise Context Resolution
```python
def verify_cpse_access(
    current_user: User = Depends(get_current_user),
) -> str
```
- **Description:** Returns the caller's CPSE tenant for Attribute-Level Privacy filtering, derived **only** from the authenticated session (`current_user.cpse`). Client-supplied fields such as the `X-CPSE-ID` header never establish tenant authority.

### F. Query Parameter Dependency Models
- [`PaginationParams`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/dependencies.py#L130-L134): Standard pagination query parameters (`skip: int = 0`, `limit: int = 100`).
- [`InventoryFilterParams`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/dependencies.py#L136-L148): Query filters (`cpse`, `depot`, `status`, `item_type`).

---

## 3. Sub-Router Index (`routers/`)

The presentation layer delegates execution to 7 specialized sub-routers in [`backend/app/api/routers/`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/routers/README.md):

| Router Module | Mount Prefix | Key Endpoints | Operational Function |
|---|---|---|---|
| [`auth.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/routers/auth.py) | `/api/v1/auth` | `/login`, `/logout`, `/me`, `/csrf`, `/seed-users`, `/users`, `/users/{id}/approve`, `/users/{id}/reject` | Username/password sign-in establishing a server-side HttpOnly session, CSRF token issue, demo personas, and admin account provisioning/approval. Public signup is retired (`POST /auth/signup` → 404); no JWT/Bearer is issued or accepted. |
| [`requisition.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/routers/requisition.py) | `/api/v1/requisition` | `/`, `/{id}/approve`, `/{id}/gatepass`, `/dispatch` | Multi-tenant scoped consignments, Segregation of Duties approvals, and CISF digital gate passes. |
| [`match.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/routers/match.py) | `/api/v1/match` | `/search`, `/benchmark` | Multi-property compatibility evaluation $S(Q, C)$, 21 deterministic safety rules, IIW Carbon Equivalent, and NACE hardness checks. |
| [`inventory.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/routers/inventory.py) | `/api/v1/inventory` | `/`, `/stats`, `/surplus`, `/hitl-queue`, `/{sku}/status` | Enterprise master stock catalog, surplus declarations, and HITL quality triage. |
| [`graph.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/routers/graph.py) | `/api/v1/graph` | `/discover`, `/topology`, `/logistics/{src}/{tgt}` | Regional surplus clustering, GIS road distance, transit hours, and inter-CPSE corridor network topology. |
| [`audit.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/routers/audit.py) | `/api/v1/audit` | `/`, `/verify`, `/export`, `/{log_id}` | Sovereign SHA-256 blockchain-style audit ledger verification and RFC 4180 CSV export for CVC/CAG statutory compliance. |
| [`ingest.py`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/backend/app/api/routers/ingest.py) | `/api/v1/ingest` | `/document`, `/catalog`, `/documents` | Dual-path PDF vector stream and PaddleOCR document ingestion, EN 10204 3.1 MTC metallurgy extraction. |

---

## 4. Usage Example: Authenticated Endpoint with RBAC & Tenancy

```python
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.app.api.dependencies import (
    get_db_session,
    get_current_user,
    require_roles,
    validate_idempotency_key,
)
from backend.app.models.tables import User

router = APIRouter(prefix="/example", tags=["Example"])

@router.post("/dispatch-material")
def dispatch_material_handler(
    payload: Dict[str, Any],
    # 1. Require Materials Manager or CISF role
    current_user: User = Depends(require_roles(["MATERIALS_MANAGER", "CISF_SECURITY"])),
    # 2. Enforce idempotency key to prevent double dispatch
    idempotency_key: str = Depends(validate_idempotency_key),
    # 3. Inject active database session
    db: Session = Depends(get_db_session),
):
    if isinstance(idempotency_key, dict) and idempotency_key.get("status") == "CACHED":
        return idempotency_key["data"]

    return {
        "status": "DISPATCH_AUTHORIZED",
        "actor": current_user.username,
        "role": current_user.role,
        "enterprise": current_user.cpse,
        "depot": current_user.depot_id,
        "consignment": payload.get("consignment_id"),
    }
```
