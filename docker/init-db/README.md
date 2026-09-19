# PostgreSQL Database Initialization Scripts (`docker/init-db/`)

This directory contains initialization SQL scripts that are automatically executed by the official PostgreSQL Docker container on its initial boot.

---

## 1. File Breakdown

### `01-init-samanvay.sql` — PostgreSQL 16 Initializer
- **Purpose:** Pre-configures the PostgreSQL `samanvay_db` instance before application tables are created.
- **Key Operations:**
  1. `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`
     - Enables Universally Unique Identifier (UUIDv4) generation functions (`uuid_generate_v4()`) for unique document, requisition, and event IDs.
  2. `CREATE EXTENSION IF NOT EXISTS "pgcrypto";`
     - Enables cryptographic hashing and HMAC functions inside PostgreSQL for sovereign cryptographic verification.
  3. `GRANT ALL PRIVILEGES ON DATABASE samanvay_db TO samanvay;`
     - Ensures the unprivileged application database user `samanvay` owns all schemas, tables, and sequences.

---

## 2. How PostgreSQL Docker Initialization Works

When the `samanvay-ai-postgres` container starts for the first time with an empty data directory:
1. PostgreSQL initializes the database cluster via `initdb`.
2. It executes all `.sql`, `.sql.gz`, and `.sh` scripts located in `/docker-entrypoint-initdb.d/` in alphabetical order.
3. The volume mount in `docker-compose.yml`:
   ```yaml
   volumes:
     - ./docker/init-db:/docker-entrypoint-initdb.d:ro
   ```
   ensures `01-init-samanvay.sql` runs before the backend microservice connects.
