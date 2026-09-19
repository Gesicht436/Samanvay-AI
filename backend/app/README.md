# Application Module (`backend/app/`)

This directory contains the internal application structure of the **Samanvay-AI** backend service, organized cleanly according to the clean-architecture layered pattern.

---

## 1. Architectural Layers

The application is structured into five distinct, decoupled layers:

1. **`api/` (Presentation & HTTP Layer):**
   - HTTP route handlers, request parsing, query parameter extraction, multi-tenant headers (`X-CPSE-ID`), and dependency injection.
2. **`core/` (Foundational Services & Security):**
   - Environment settings, global exception handlers, and cryptographic hash chain primitives.
3. **`models/` (Relational Persistence Layer):**
   - SQLAlchemy Declarative ORM models defining the database schema, foreign keys, and indexes.
4. **`schemas/` (Data Transfer Objects & Contracts):**
   - Pydantic v2 data contracts enforcing strict validation for requests and responses.
5. **`services/` (Domain Business Logic Layer):**
   - Transactional execution, pessimistic database locking, CDC event processing, and sovereign audit hashing.

---

## 2. Directory Layout

```
backend/app/
├── __init__.py               # Package marker
├── api/                      # Presentation layer (dependencies & endpoint routers)
├── core/                     # Configuration, errors, cryptographic hashing
├── models/                   # SQLAlchemy declarative tables
├── schemas/                  # Pydantic v2 validation contracts
└── services/                 # Business logic and external engine orchestrators
```
