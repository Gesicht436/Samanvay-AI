-- ==============================================================================
-- Samanvay-AI: PostgreSQL 16 Initialization Script
-- Project: Samanvay-AI (MoPNG / BharatCodex)
-- ==============================================================================

-- Enable standard cryptographic extensions for SHA-256 audit sealing & UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Ensure application user has ownership & privileges
GRANT ALL PRIVILEGES ON DATABASE samanvay_db TO samanvay;

COMMENT ON DATABASE samanvay_db IS 'Samanvay-AI Relational Master Ledger & Inventory Database';
