# Relational Database Models (`backend/app/models/`)

This directory contains the **SQLAlchemy 2.0 Declarative ORM** schema definitions representing tables in PostgreSQL 16.

---

## 1. File-by-File Breakdown

### `base.py` — Database Engine & Session Provider
- **Purpose:** Initializes SQLAlchemy engine, sessionmaker, and declarative base.
- **Key Functions & Classes:**
  - `Base`: `DeclarativeBase` subclass with shared helper methods.
  - `get_db() -> Generator[Session, None, None]`: Contextual database session dependency yielding transactional sessions with automatic commit/rollback.
  - `init_db()`: Creates all database tables if they do not exist.

### `tables.py` — Database Table Definitions
- **Purpose:** Codifies tables, constraints, foreign keys, and indexes.
- **Key ORM Models:**
  - `InventoryItem`:
    - `sku_code`: Primary key (e.g. `IOCL-PR-VLV-0001`).
    - `cpse`: Owning enterprise (`IOCL`, `ONGC`, etc.).
    - `depot_location`: Storage warehouse location.
    - `description`: Full engineering item text description.
    - `item_type`, `nominal_size`, `pressure_class`, `material_grade`, `schedule`, `facing`, `trim`.
    - `quantity_on_hand`, `quantity_reserved`, `unit_of_measure`.
    - `status`: `AVAILABLE`, `RESERVED`, `DISPATCHED`, `SCRAPPED`.
    - `is_surplus`: Boolean flag indicating non-moving idle inventory.
    - `unit_price_inr`: Procurement book value (confidential; stripped during cross-CPSE sharing).
  - `Requisition`:
    - `requisition_id`: Unique requisition identifier (e.g. `REQ-2026-0082`).
    - `requesting_cpse`: Enterprise requesting the material.
    - `target_item_type`, `required_size`, `required_class`, `required_material`.
    - `quantity_requested`: Number of units required.
    - `matched_sku_code`: Foreign key to `InventoryItem` (if matched).
    - `supplying_cpse`: Enterprise supplying surplus stock.
    - `urgency`: `ROUTINE`, `URGENT`, `EMERGENCY_SHUTDOWN`.
    - `status`: `PENDING`, `MATCHED`, `APPROVED`, `DISPATCHED`, `COMPLETED`, `CANCELLED`.
    - `idempotency_key`: Unique constraint preventing duplicate order creation.
  - `IngestedDocument`:
    - `doc_id`: Unique document UUID.
    - `filename`, `file_type`, `file_size_bytes`.
    - `raw_text`, `ocr_status`, `parsed_attributes` (JSONB).
  - `SovereignAuditLedger`:
    - `entry_id`: Monotonically increasing sequence integer.
    - `timestamp`: UTC ISO timestamp.
    - `actor`: Identification of user, system process, or external CPSE.
    - `action_type`: Category of operation (`MATCH_SEARCH`, `INVENTORY_LOCK`, `REQUISITION_DISPATCH`, etc.).
    - `previous_hash`: SHA-256 hash of preceding ledger row.
    - `entry_hash`: SHA-256 hash of current block.
    - `payload_json`: JSONB data payload.
  - `CDCPendingEvent`:
    - `event_id`: Primary key.
    - `table_name`, `record_key`, `operation` (`INSERT`, `UPDATE`, `DELETE`).
    - `status`: `PENDING`, `SYNCED`, `FAILED`.

---

## 2. ER Diagram

```
┌────────────────────────┐                ┌─────────────────────────┐
│     InventoryItem      │                │       Requisition       │
├────────────────────────┤                ├─────────────────────────┤
│ PK sku_code            │1              *│ PK requisition_id       │
│    cpse                ├────────────────┤ FK matched_sku_code     │
│    depot_location      │                │    requesting_cpse      │
│    quantity_on_hand    │                │    supplying_cpse       │
│    quantity_reserved   │                │    status               │
│    status              │                │    idempotency_key (UQ) │
└────────────────────────┘                └─────────────────────────┘
            │
            │ Triggers via CDC
            ▼
┌────────────────────────┐                ┌─────────────────────────┐
│    CDCPendingEvent     │                │   SovereignAuditLedger  │
├────────────────────────┤                ├─────────────────────────┤
│ PK event_id            │                │ PK entry_id (Seq)       │
│    table_name          │                │    timestamp            │
│    operation           │                │    previous_hash        │
│    status              │                │    entry_hash           │
└────────────────────────┘                └─────────────────────────┘
```
