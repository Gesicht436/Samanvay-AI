# PostgreSQL Database Initialization Scripts

This folder contains container initialization scripts automatically executed by the official PostgreSQL Docker image entrypoint (`/docker-entrypoint-initdb.d/`) upon first volume creation.

---

## File Breakdown

### 1. `01-init-samanvay.sql`
- **UUID & Cryptographic Extensions**:
  - `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";` - Enables native RFC 4122 UUID generation for item and consignment identifiers.
  - `CREATE EXTENSION IF NOT EXISTS "pgcrypto";` - Provides cryptographic hashing functions (SHA-256) used for immutability verification and password hashing.
- **Role Privileges**:
  - `GRANT ALL PRIVILEGES ON DATABASE samanvay_db TO samanvay;` - Confirms root application privileges on the relational ledger.
- **Database Comment**:
  - Tags the database with sovereign project metadata: `'Samanvay-AI Relational Master Ledger & Inventory Database'`.
