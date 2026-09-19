# Domain Business Logic & Services (`backend/app/services/`)

This directory contains the business logic layer, database transactional coordination, Change Data Capture (CDC) processing, and cryptographic ledger services.

---

## 1. File-by-File Breakdown

### `requisition_service.py` — Requisition & Order Processing
- **Purpose:** Coordinates requisition creation, status transitions, and inventory reservation.
- **Key Functions:**
  - `create_requisition(db, request, idempotency_key)`:
    - Checks for existing idempotency key to prevent double allocation.
    - Uses **Pessimistic Row-Level Locking (`SELECT ... FOR UPDATE`)** on `InventoryItem` to reserve inventory stock without race conditions under high concurrent demand.
    - Increments `quantity_reserved` and updates item status.
    - Appends an entry to `SovereignAuditLedger`.
  - `approve_requisition(db, req_id)`: Transitions order to `APPROVED`.
  - `dispatch_requisition(db, req_id)`: Generates cryptographic gate pass seal and transitions status to `DISPATCHED`.

### `inventory_service.py` — Inventory & Privacy Enforcement
- **Purpose:** Queries catalog items, filters surplus, and enforces cross-enterprise data privacy.
- **Key Functions:**
  - `list_inventory(db, cpse, status, pagination)`: Retrieves paginated items.
  - `get_item(db, sku_code, requesting_cpse)`:
    - **Attribute-Level Privacy Stripping:** If `requesting_cpse` is different from the owning CPSE, masks proprietary unit acquisition prices (`unit_price_inr = None`).

### `audit_service.py` — Sovereign Audit Ledger Engine
- **Purpose:** Maintains the cryptographic SHA-256 blockchain-style hash chain.
- **Key Functions & Classes:**
  - `create_audit_entry(db, request)`:
    - Fetches the `entry_hash` of the most recent block (or `AUDIT_GENESIS_HASH` if ledger is empty).
    - Calculates the new chained SHA-256 hash incorporating previous hash, timestamp, actor, action, and JSON payload.
    - Commits the record.
  - `verify_ledger_integrity(db)`:
    - Traverses all entries in order of `entry_id`.
    - Recalculates expected hash for every row.
    - If any past row was modified or deleted, detects the tampering index immediately.
  - `export_audit_csv(db)`: Exports records in strict RFC 4180 CSV format.

### `cdc_manager.py` — Change Data Capture (CDC) Worker
- **Purpose:** Synchronizes PostgreSQL relational state to the Neo4j Knowledge Graph.
- **Key Functions:**
  - `init_cdc_schema()`: Ensures pending event queues exist.
  - `process_pending_events(syncer, limit=100) -> int`:
    - Polls `CDCPendingEvent` rows with `status='PENDING'`.
    - Replays changes into Neo4j graph nodes and edges via `Neo4jSyncer`.
    - Updates event status to `SYNCED`.
  - `backfill_graph_if_empty(syncer)`: Backfills Neo4j from relational database on first boot.

### `seeder.py` — Cold-Start Database Seeder
- **Purpose:** Automatically seeds PostgreSQL with realistic public sector inventory data from `data/inventory_catalog.csv` upon first boot.
- **Key Functions:**
  - `derive_depot_id(cpse, location) -> str`: Normalizes location codes.
  - `seed_database_if_empty()`: Populates inventory items, depots, and plants if the table is empty.

---

## 2. Concurrency Safety: Pessimistic Locking

To prevent two CPSEs from simultaneously reserving the last remaining surplus valve:

```python
# Requisition service concurrency pattern:
candidate_item = db.query(InventoryItem).filter(
    InventoryItem.sku_code == sku_code
).with_for_update().first()

if candidate_item.quantity_on_hand - candidate_item.quantity_reserved < requested_qty:
    raise InsufficientInventoryError("Stock was reserved by a concurrent transaction")

candidate_item.quantity_reserved += requested_qty
db.commit()
```
