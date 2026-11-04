# Dependency Injection & Controller Middleware (`backend/app/api/`)

## 1. Architectural Role & Overview

The `backend/app/api/` package provides reusable **FastAPI dependency injectors**, zero-trust security middleware, session authentication checkers, centralized authorization policy gates, database session providers, and request validators used across all REST routers.

It guarantees that every incoming HTTP request satisfies prerequisite contracts: valid server-side session cookies, CSRF protection, fine-grained permission grants, enterprise CPSE tenancy scoping, idempotency guarantees, and connection pooling to PostgreSQL and Qdrant.

```mermaid
flowchart TD
    Req["Incoming HTTP Request"] --> CookieCheck{"Has Session Cookie?<br>(__Host-samanvay_session)"}

    CookieCheck -->|Yes| SessionLookup["dependencies.py: get_current_session()<br>(SHA-256 Token Lookup in auth_sessions)"]
    SessionLookup --> OutcomeCheck{"Session Status == 'live'?"}
    OutcomeCheck -->|No| ClearCookie["401 Unauthorized + Set-Cookie Deletion Header"]
    OutcomeCheck -->|Yes| UserVerify["get_current_user: DB Lookup<br>(is_active=True & is_approved=True)"]

    CookieCheck -->|No| DenyAuth["401 Unauthorized (No Credential)"]

    UserVerify --> CSRFGate{"State-Changing Request?<br>(require_csrf)"}
    CSRFGate -->|Yes| CSRFCheck{"Origin in Allowlist &&<br>X-CSRF-Token Matches Session?"}
    CSRFCheck -->|No| CSRFDeny["403 Forbidden (CSRF_ORIGIN / CSRF_TOKEN_DENIED)"]
    CSRFCheck -->|Yes| PermGate{"require_permission(permission)"}
    CSRFGate -->|No (GET/HEAD)| PermGate

    PermGate --> PolicyEval["Centralized Policy Evaluation (AUTH-007)<br>evaluate(Subject, Action, Resource, Context)"]
    PolicyEval -->|ALLOW| TenantCheck["verify_cpse_access(): Authoritative CPSE Scoping"]
    PolicyEval -->|DENY| DenyPerm["403 Forbidden + SecurityEvent Logged"]

    TenantCheck --> Handler["Router Endpoint Execution"]

    Handler --> DBSession["get_db_session(): Yields SQLAlchemy Session"]
    Handler --> VectorSearch["deps.py: get_vector_searcher() (Qdrant + BGE-M3)"]
```

---

## 2. Module Inventory

| File | Primary Functions & Classes | Responsibility |
| :--- | :--- | :--- |
| [`dependencies.py`](file:///C:/Users/mayank/Development/Hackathons/Samanvay-AI/backend/app/api/dependencies.py) | `get_db_session()`, `get_current_session()`, `get_current_user()`, `require_permission()`, `require_any_permission()`, `require_csrf()`, `verify_cpse_access()`, `validate_idempotency_key()`, `PaginationParams`, `InventoryFilterParams` | Provides core zero-trust dependency injection: server session authentication, CSRF origin/token verification, centralized RBAC/ABAC policy enforcement, tenant resolution, and idempotency guarantees. |
| [`deps.py`](file:///C:/Users/mayank/Development/Hackathons/Samanvay-AI/backend/app/api/deps.py) | `get_vector_searcher()`, `audit_context()` | LRU-cached dependency for the vector search engine (`VectorSearcher`), verifying on-disk model weights and falling back to embedded local Qdrant if the server is offline. |
| [`routers/`](file:///C:/Users/mayank/Development/Hackathons/Samanvay-AI/backend/app/api/routers/README.md) | Subpackage | REST endpoint routers (`match`, `inventory`, `requisition`, `ingest`, `graph`, `audit`, `auth`). |
| [`v1/`](file:///C:/Users/mayank/Development/Hackathons/Samanvay-AI/backend/app/api/v1/README.md) | Subpackage | Contract-driven endpoints, system readiness dashboard (`/summary`), and active learning queues. |
| [`__init__.py`](file:///C:/Users/mayank/Development/Hackathons/Samanvay-AI/backend/app/api/__init__.py) | Package initialization | Namespace anchor. |

---

## 3. Dependency Specifications

### 3.1. Zero-Trust Session Authentication (`dependencies.py`)

- **`get_current_session`**:
  - Intercepts `__Host-samanvay_session` (production) or `samanvay_session` (development) cookie.
  - Hashes the presented 256-bit entropy token using SHA-256 and queries `auth_sessions`.
  - Rejects missing, expired, revoked, or unknown sessions with `HTTP 401 Unauthorized` and returns an immediate cookie-clearing header (`session_cookie_deletion_header`).
  - Emits sanitized `LOGIN_FAILURE` security telemetry for invalid presentation attempts.
- **`get_current_user`**:
  - Chains onto `get_current_session`.
  - Verifies `user.is_active == True` and `user.is_approved == True`.
  - Updates `last_seen_at` on the active session.
  - Returns the strongly-typed `User` ORM instance.

### 3.2. Centralized Authorization & Permission Gates (`require_permission`)

- **`require_permission(permission: str)`**:
  - Enforces the frozen canonical permission matrix (AUTH-007).
  - Invokes `backend.app.core.authorization.evaluate()` with the caller's role, requested permission, and CPSE context.
  - Returns HTTP 403 with structured machine-readable error reasons (e.g. `{"error": "AUTHORIZATION_DENIED", "reason": "PERMISSION_NOT_GRANTED"}`).
  - Records an authoritative `AUTHORIZATION_FAILURE` record in `security_events`.
- **`require_any_permission(*permissions)`**:
  - Grants access if the caller holds *any* of the specified permissions.

### 3.3. Strict CSRF Defense (`require_csrf`)

- Required on all mutating requests (`POST`, `PUT`, `DELETE`).
- **Origin Check**: Verifies that the browser's `Origin` header exists in `settings.allowed_origins_list`. Never trusts client-controlled `Host` headers.
- **Token Verification**: Computes HMAC of the session's token hash and compares with the incoming `X-CSRF-Token` header.
- Rejection emits an explicit `AUTHORIZATION_FAILURE` security event with `reason="CSRF_ORIGIN_DENIED"` or `reason="CSRF_TOKEN_DENIED"`.

### 3.4. Authoritative Multi-Tenant Enterprise Resolution (`verify_cpse_access`)

- Determines the caller's enterprise identity for attribute-level privacy and query scoping.
- **Strict Invariant**: Tenant authority is derived **exclusively** from `current_user.cpse` (the session-authenticated identity).
- Client-supplied parameters (e.g., query params, request bodies, or spoofed `X-CPSE-ID` headers) are **never** permitted to broaden or switch tenant authority.

### 3.5. Financial Idempotency Protection (`validate_idempotency_key`)
- Reads the `Idempotency-Key` header on mutating POST/PUT endpoints.
- Queries `idempotency_keys` table.
- If an unexpired matching record is found, returns `{"status": "CACHED", "data": ...}` to immediately short-circuit redundant double-debits or duplicate consignments.

### 3.6. Cached Vector Search Engine (`deps.py`)
- **`get_vector_searcher()`**:
  - Decorated with `@lru_cache(maxsize=1)` to avoid re-instantiating heavy ML transformers on every search request.
  - Verifies that `settings.model_weights_path` contains an ONNX or Hugging Face directory.
  - Attempts network connection to `qdrant_host:qdrant_port`. If unreachable (e.g. offline field laptop), automatically falls back to an embedded SQLite-backed local client (`QdrantClient(path=settings.qdrant_local_path)`).
