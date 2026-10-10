"""FROZEN baseline DDL for Alembic revision 0001.

GENERATED FILE -- do not edit by hand.  Regenerated from the ORM metadata by
the one-shot generator used when the migration tooling was introduced.  These
are the exact statements the 0001 baseline applies and the same strings the
adoption/startup verification parses when comparing a live database.

Session digest storage is enforced by construction: auth_sessions carries
``session_token_hash VARCHAR(64)`` and no raw-secret column exists.
"""

BASELINE_STATEMENTS = [
    'CREATE TABLE active_learning_feedback (\n\tid SERIAL NOT NULL, \n\tsource_description TEXT NOT NULL, \n\tsource_sku VARCHAR(64) NOT NULL, \n\tcanonical_id VARCHAR(64) NOT NULL, \n\tdecision VARCHAR(16) NOT NULL, \n\tofficer VARCHAR(128) NOT NULL, \n\taction_note TEXT, \n\ttier_override VARCHAR(32), \n\tconfidence_override NUMERIC(5, 4), \n\tcreated_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (id)\n)',
    'CREATE TABLE cdc_outbox (\n\tid SERIAL NOT NULL, \n\ttable_name VARCHAR(64) NOT NULL, \n\toperation VARCHAR(16) NOT NULL, \n\trecord_id VARCHAR(128) NOT NULL, \n\tpayload JSONB NOT NULL, \n\tstatus VARCHAR(20) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE, \n\tprocessed_at TIMESTAMP WITH TIME ZONE, \n\terror_message TEXT, \n\tPRIMARY KEY (id)\n)',
    'CREATE TABLE idempotency_keys (\n\tkey VARCHAR(128) NOT NULL, \n\tendpoint VARCHAR(255) NOT NULL, \n\trequest_hash VARCHAR(64) NOT NULL, \n\tstatus_code INTEGER NOT NULL, \n\tresponse_body JSONB NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (key)\n)',
    'CREATE TABLE ingested_documents (\n\tid SERIAL NOT NULL, \n\tfilename VARCHAR(255) NOT NULL, \n\tdoc_type VARCHAR(64) NOT NULL, \n\tis_scanned BOOLEAN, \n\tconfidence NUMERIC(5, 4) NOT NULL, \n\traw_text TEXT, \n\tparsed_metadata JSONB NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (id)\n)',
    'CREATE TABLE sovereign_audit_ledger (\n\tlog_id VARCHAR(64) NOT NULL, \n\ttimestamp TIMESTAMP WITH TIME ZONE, \n\taction_category VARCHAR(64) NOT NULL, \n\taction_name VARCHAR(128) NOT NULL, \n\tactor_name VARCHAR(128) NOT NULL, \n\tactor_role VARCHAR(128) NOT NULL, \n\tcpse VARCHAR(32) NOT NULL, \n\tdepot VARCHAR(255) NOT NULL, \n\treference_id VARCHAR(128) NOT NULL, \n\tdetails TEXT NOT NULL, \n\tprev_hash VARCHAR(64) NOT NULL, \n\tsha256_hash VARCHAR(64) NOT NULL, \n\tis_verified BOOLEAN, \n\tPRIMARY KEY (log_id)\n)',
    'CREATE TABLE users (\n\tid SERIAL NOT NULL, \n\tusername VARCHAR(64) NOT NULL, \n\temail VARCHAR(128), \n\thashed_password VARCHAR(255) NOT NULL, \n\tfull_name VARCHAR(128) NOT NULL, \n\trole VARCHAR(64) NOT NULL, \n\tcpse VARCHAR(32) NOT NULL, \n\tdepot_id VARCHAR(64) NOT NULL, \n\tis_active BOOLEAN DEFAULT true NOT NULL, \n\tis_approved BOOLEAN DEFAULT false NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (id), \n\tUNIQUE (email)\n)',
    'CREATE TABLE auth_sessions (\n\tid UUID NOT NULL, \n\tsession_token_hash VARCHAR(64) NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tlast_seen_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\trevoked_at TIMESTAMP WITH TIME ZONE, \n\tip_address VARCHAR(64), \n\tuser_agent VARCHAR(512), \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE\n)',
    'CREATE TABLE inventory_items (\n\tid SERIAL NOT NULL, \n\tsku_code VARCHAR(64) NOT NULL, \n\tcpse VARCHAR(32) NOT NULL, \n\tdepot_id VARCHAR(64) NOT NULL, \n\tdepot_location VARCHAR(255) NOT NULL, \n\tpo_no VARCHAR(128), \n\theat_no VARCHAR(128), \n\tdescription TEXT NOT NULL, \n\tcanonical_id VARCHAR(64), \n\titem_type VARCHAR(64) NOT NULL, \n\tsize_nb_mm NUMERIC(8, 2), \n\tpressure_class INTEGER, \n\tpressure_rating_psi NUMERIC(10, 2), \n\tschedule VARCHAR(32), \n\tmetallurgy VARCHAR(64), \n\tfacing_end VARCHAR(32), \n\tstandard VARCHAR(64), \n\tindian_standard VARCHAR(100), \n\toil_std_spec VARCHAR(100), \n\toil_material_code VARCHAR(32), \n\tgem_category_id VARCHAR(100), \n\tgem_product_id VARCHAR(64), \n\tcppp_tender_ref VARCHAR(100), \n\tmake_in_india_class VARCHAR(32), \n\tlocal_content_percentage NUMERIC(5, 2), \n\tpressure_rating_bar NUMERIC(8, 2), \n\tlocation_state VARCHAR(64), \n\tproperties JSONB, \n\tquantity INTEGER NOT NULL, \n\tunit_cost_inr NUMERIC(14, 2) NOT NULL, \n\ttotal_value_inr NUMERIC(14, 2) GENERATED ALWAYS AS (quantity * unit_cost_inr) STORED, \n\tstatus VARCHAR(32) NOT NULL, \n\tdays_idle INTEGER, \n\tsource_document_id INTEGER, \n\tis_broadcasted_surplus BOOLEAN, \n\tcreated_at TIMESTAMP WITH TIME ZONE, \n\tupdated_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (id), \n\tCONSTRAINT ck_quantity_non_negative CHECK (quantity >= 0), \n\tFOREIGN KEY(source_document_id) REFERENCES ingested_documents (id)\n)',
    'CREATE TABLE requisitions (\n\trequisition_id VARCHAR(64) NOT NULL, \n\tsource_cpse VARCHAR(32) NOT NULL, \n\tsource_depot VARCHAR(255) NOT NULL, \n\tsource_unit VARCHAR(128) NOT NULL, \n\ttarget_cpse VARCHAR(32) NOT NULL, \n\ttarget_depot VARCHAR(255) NOT NULL, \n\tsku_code VARCHAR(64) NOT NULL, \n\titem_description TEXT NOT NULL, \n\trequired_qty INTEGER NOT NULL, \n\tunit_cost_inr NUMERIC(14, 2) NOT NULL, \n\ttotal_value_inr NUMERIC(14, 2) NOT NULL, \n\tjustification TEXT NOT NULL, \n\turgency_level VARCHAR(32) NOT NULL, \n\tstatus VARCHAR(32) NOT NULL, \n\trequested_by VARCHAR(128) NOT NULL, \n\tapproved_by VARCHAR(128), \n\tapproved_at TIMESTAMP WITH TIME ZONE, \n\trejection_reason TEXT, \n\tdispatch_timestamp TIMESTAMP WITH TIME ZONE, \n\tdelivery_timestamp TIMESTAMP WITH TIME ZONE, \n\taudit_hash VARCHAR(64) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (requisition_id), \n\tCONSTRAINT ck_required_qty_positive CHECK (required_qty > 0), \n\tFOREIGN KEY(sku_code) REFERENCES inventory_items (sku_code)\n)',
    'CREATE TABLE security_events (\n\tid UUID NOT NULL, \n\tevent_type VARCHAR(64) NOT NULL, \n\tuser_id INTEGER, \n\tsession_id UUID, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tsuccess BOOLEAN NOT NULL, \n\tip_address VARCHAR(64), \n\tuser_agent VARCHAR(512), \n\tmetadata JSONB NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL, \n\tFOREIGN KEY(session_id) REFERENCES auth_sessions (id) ON DELETE SET NULL\n)',
    'CREATE TABLE digital_gate_passes (\n\tgate_pass_no VARCHAR(64) NOT NULL, \n\trequisition_id VARCHAR(64) NOT NULL, \n\tissuing_cpse VARCHAR(32) NOT NULL, \n\tissuing_depot VARCHAR(255) NOT NULL, \n\treceiving_cpse VARCHAR(32) NOT NULL, \n\treceiving_depot VARCHAR(255) NOT NULL, \n\ttransporter_name VARCHAR(128) NOT NULL, \n\tvehicle_no VARCHAR(32) NOT NULL, \n\tdriver_name VARCHAR(128) NOT NULL, \n\tdriver_id_no VARCHAR(64) NOT NULL, \n\tgst_eway_bill_no VARCHAR(64) NOT NULL, \n\tcisf_verification_seal VARCHAR(128) NOT NULL, \n\tissue_timestamp TIMESTAMP WITH TIME ZONE, \n\tsha256_hash VARCHAR(64) NOT NULL, \n\ttransit_distance_km NUMERIC(10, 2) NOT NULL, \n\tco2_saved_kg NUMERIC(10, 2) NOT NULL, \n\testimated_transit_hours INTEGER NOT NULL, \n\tqr_code_svg TEXT NOT NULL, \n\tPRIMARY KEY (gate_pass_no), \n\tFOREIGN KEY(requisition_id) REFERENCES requisitions (requisition_id)\n)',
    'CREATE TABLE inventory_locks (\n\tid SERIAL NOT NULL, \n\tsku_code VARCHAR(64) NOT NULL, \n\trequisition_id VARCHAR(64) NOT NULL, \n\tlocked_qty INTEGER NOT NULL, \n\tlocked_at TIMESTAMP WITH TIME ZONE, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tis_active BOOLEAN, \n\tPRIMARY KEY (id), \n\tCONSTRAINT ck_locked_qty_positive CHECK (locked_qty > 0), \n\tFOREIGN KEY(sku_code) REFERENCES inventory_items (sku_code), \n\tFOREIGN KEY(requisition_id) REFERENCES requisitions (requisition_id)\n)',
    'CREATE INDEX ix_active_learning_feedback_canonical_id ON active_learning_feedback (canonical_id)',
    'CREATE INDEX ix_active_learning_feedback_source_sku ON active_learning_feedback (source_sku)',
    'CREATE INDEX ix_cdc_outbox_created_at ON cdc_outbox (created_at)',
    'CREATE INDEX ix_cdc_outbox_record_id ON cdc_outbox (record_id)',
    'CREATE INDEX ix_cdc_outbox_status ON cdc_outbox (status)',
    'CREATE INDEX ix_cdc_outbox_table_name ON cdc_outbox (table_name)',
    'CREATE INDEX ix_users_cpse ON users (cpse)',
    'CREATE INDEX ix_users_depot_id ON users (depot_id)',
    'CREATE UNIQUE INDEX ix_users_username ON users (username)',
    'CREATE UNIQUE INDEX ix_auth_sessions_session_token_hash ON auth_sessions (session_token_hash)',
    'CREATE INDEX ix_auth_sessions_user_expires_active ON auth_sessions (user_id, expires_at) WHERE revoked_at IS NULL',
    'CREATE INDEX ix_inventory_items_cpse ON inventory_items (cpse)',
    'CREATE INDEX ix_inventory_items_depot_id ON inventory_items (depot_id)',
    'CREATE INDEX ix_inventory_items_gem_category_id ON inventory_items (gem_category_id)',
    'CREATE INDEX ix_inventory_items_indian_standard ON inventory_items (indian_standard)',
    'CREATE INDEX ix_inventory_items_item_type ON inventory_items (item_type)',
    'CREATE INDEX ix_inventory_items_oil_material_code ON inventory_items (oil_material_code)',
    'CREATE UNIQUE INDEX ix_inventory_items_sku_code ON inventory_items (sku_code)',
    'CREATE INDEX ix_inventory_items_status ON inventory_items (status)',
    'CREATE INDEX ix_security_events_event_type ON security_events (event_type)',
    'CREATE INDEX ix_security_events_session_created ON security_events (session_id, created_at)',
    'CREATE INDEX ix_security_events_type_created ON security_events (event_type, created_at)',
    'CREATE INDEX ix_security_events_user_created ON security_events (user_id, created_at)',
]

# ── Baseline identity ──────────────────────────────────────────────────────────
BASELINE_REVISION = "0001"

# Tables in reverse-dependency (teardown-safe) order, matching
# ``reversed(list(Base.metadata.sorted_tables))`` from the ORM metadata.
BASELINE_TABLES = [
    "inventory_locks",
    "digital_gate_passes",
    "security_events",
    "requisitions",
    "inventory_items",
    "auth_sessions",
    "users",
    "sovereign_audit_ledger",
    "ingested_documents",
    "idempotency_keys",
    "cdc_outbox",
    "active_learning_feedback",
]

