"""
Samanvay-AI Real-Time Change Data Capture (CDC) Manager & Worker.

Listens to PostgreSQL changes via transactional triggers & LISTEN/NOTIFY,
and immediately mirrors row creations, updates, and requisitions into
the Neo4j Knowledge Graph in sub-millisecond real-time.
"""

import os
import sys
import json
import time
import select
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import psycopg2
import psycopg2.extensions
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.base import engine, SessionLocal
from backend.app.models.tables import InventoryItem, Requisition, CdcOutbox
from graph.syncer import Neo4jSyncer

logger = logging.getLogger("samanvay.cdc")


def init_cdc_schema():
    """Initializes the cdc_outbox table and PostgreSQL transactional triggers."""
    with engine.begin() as conn:
        # Create outbox table if not exists
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS cdc_outbox (
            id BIGSERIAL PRIMARY KEY,
            table_name VARCHAR(64) NOT NULL,
            operation VARCHAR(16) NOT NULL,
            record_id VARCHAR(128) NOT NULL,
            payload JSONB NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            processed_at TIMESTAMP WITH TIME ZONE,
            error_message TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_cdc_outbox_status_id ON cdc_outbox (status, id);
        """))

        # Create Trigger Function
        conn.execute(text("""
        CREATE OR REPLACE FUNCTION fn_cdc_capture() RETURNS TRIGGER AS $$
        DECLARE
            rec_id TEXT;
            payload_json JSONB;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                payload_json := to_jsonb(OLD);
            ELSE
                payload_json := to_jsonb(NEW);
            END IF;

            IF TG_TABLE_NAME = 'inventory_items' THEN
                rec_id := payload_json->>'sku_code';
            ELSIF TG_TABLE_NAME = 'requisitions' THEN
                rec_id := payload_json->>'requisition_id';
            ELSE
                rec_id := 'UNKNOWN';
            END IF;

            INSERT INTO cdc_outbox (table_name, operation, record_id, payload, status, created_at)
            VALUES (TG_TABLE_NAME, TG_OP, rec_id, payload_json, 'PENDING', NOW());

            PERFORM pg_notify('samanvay_cdc_channel', json_build_object(
                'table', TG_TABLE_NAME,
                'op', TG_OP,
                'record_id', rec_id
            )::text);

            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            ELSE
                RETURN NEW;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """))

        # Attach Triggers to inventory_items and requisitions
        conn.execute(text("""
        DROP TRIGGER IF EXISTS trg_inventory_cdc ON inventory_items;
        CREATE TRIGGER trg_inventory_cdc
        AFTER INSERT OR UPDATE OR DELETE ON inventory_items
        FOR EACH ROW EXECUTE FUNCTION fn_cdc_capture();

        DROP TRIGGER IF EXISTS trg_requisition_cdc ON requisitions;
        CREATE TRIGGER trg_requisition_cdc
        AFTER INSERT OR UPDATE OR DELETE ON requisitions
        FOR EACH ROW EXECUTE FUNCTION fn_cdc_capture();
        """))

    logger.info("[CDC] PostgreSQL CDC triggers and outbox initialized successfully.")


def backfill_graph_if_empty(syncer: Neo4jSyncer):
    """
    Checks if Neo4j has inventory items; if empty, backfills existing PostgreSQL catalog.
    """
    with syncer.driver.session() as session:
        res = session.run("MATCH (i:InventoryItem) RETURN count(i) as count")
        graph_count = res.single()["count"]

    if graph_count > 0:
        logger.info(f"[CDC] Neo4j already contains {graph_count} inventory nodes. Skipping initial backfill.")
        return

    logger.info("[CDC] Neo4j inventory is empty. Starting high-throughput initial backfill from PostgreSQL...")
    db: Session = SessionLocal()
    try:
        items = db.query(InventoryItem).all()
        if not items:
            logger.info("[CDC] No items found in PostgreSQL to backfill.")
            return

        prepared = []
        for i in items:
            prepared.append({
                "sku_code": i.sku_code,
                "cpse": i.cpse,
                "depot_id": i.depot_id,
                "depot_location": i.depot_location,
                "description": i.description,
                "item_type": i.item_type,
                "size_nb_mm": float(i.size_nb_mm) if i.size_nb_mm else None,
                "pressure_class": i.pressure_class,
                "schedule": i.schedule,
                "metallurgy": i.metallurgy,
                "facing_end": i.facing_end,
                "quantity": i.quantity,
                "unit_cost_inr": float(i.unit_cost_inr) if i.unit_cost_inr else 0.0,
                "total_value_inr": float(i.total_value_inr) if i.total_value_inr else 0.0,
                "status": i.status,
                "days_idle": i.days_idle,
                "is_broadcasted_surplus": i.is_broadcasted_surplus,
            })

        syncer.batch_sync_inventory(prepared, batch_size=500)
        logger.info(f"[CDC] Successfully backfilled {len(prepared)} inventory items into Neo4j graph!")

        # Also sync existing requisitions
        reqs = db.query(Requisition).all()
        for r in reqs:
            syncer.sync_requisition({
                "requisition_id": r.requisition_id,
                "source_cpse": r.source_cpse,
                "target_cpse": r.target_cpse,
                "source_depot": r.source_depot,
                "target_depot": r.target_depot,
                "sku_code": r.sku_code,
                "required_qty": r.required_qty,
                "unit_cost_inr": float(r.unit_cost_inr) if r.unit_cost_inr else 0.0,
                "total_value_inr": float(r.total_value_inr) if r.total_value_inr else 0.0,
                "status": r.status,
                "urgency_level": r.urgency_level,
                "justification": r.justification,
                "requested_by": r.requested_by,
                "approved_by": r.approved_by,
                "audit_hash": r.audit_hash,
            })
        if reqs:
            logger.info(f"[CDC] Backfilled {len(reqs)} active requisitions into Neo4j graph.")

    finally:
        db.close()


def process_pending_events(syncer: Neo4jSyncer, limit: int = 100) -> int:
    """Fetches and processes pending events from cdc_outbox."""
    db: Session = SessionLocal()
    processed_count = 0
    try:
        events = db.query(CdcOutbox).filter(CdcOutbox.status == "PENDING").order_by(CdcOutbox.id.asc()).limit(limit).all()
        if not events:
            return 0

        for ev in events:
            try:
                syncer.sync_event(ev.table_name, ev.operation, ev.payload)
                ev.status = "PROCESSED"
                ev.processed_at = datetime.now(timezone.utc)
                processed_count += 1
            except Exception as e:
                logger.error(f"[CDC] Failed to sync outbox event #{ev.id} ({ev.table_name} {ev.operation}): {e}")
                ev.status = "FAILED"
                ev.error_message = str(e)
                ev.processed_at = datetime.now(timezone.utc)

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"[CDC] Outbox batch processing error: {e}")
    finally:
        db.close()

    return processed_count


def start_cdc_worker(stop_event=None):
    """
    Main CDC Worker Loop.
    Uses PostgreSQL LISTEN/NOTIFY for instantaneous sub-millisecond push notification,
    with automatic reconnection and outbox queue draining.
    """
    logger.info("[CDC WORKER] Initializing Samanvay-AI Change Data Capture Engine...")
    init_cdc_schema()

    syncer = Neo4jSyncer()
    backfill_graph_if_empty(syncer)

    # Drain any backlog from outbox
    initial_drained = process_pending_events(syncer, limit=500)
    if initial_drained > 0:
        logger.info(f"[CDC WORKER] Drained {initial_drained} backlog outbox events on startup.")

    # Establish raw psycopg2 connection for LISTEN
    dsn_params = {
        "host": settings.postgres_host,
        "port": settings.postgres_port,
        "user": settings.postgres_user,
        "password": settings.postgres_password,
        "dbname": settings.postgres_db,
    }

    logger.info(f"[CDC WORKER] Subscribing to PostgreSQL channel 'samanvay_cdc_channel' at {dsn_params['host']}:{dsn_params['port']}...")

    while True:
        if stop_event and stop_event.is_set():
            logger.info("[CDC WORKER] Stop event detected. Exiting worker loop.")
            break

        try:
            conn = psycopg2.connect(**dsn_params)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute("LISTEN samanvay_cdc_channel;")
            logger.info("[CDC WORKER] Successfully connected and listening for real-time events.")

            while True:
                if stop_event and stop_event.is_set():
                    break

                # Wait for notifications with a 2-second timeout (acts as fallback poll)
                if select.select([conn], [], [], 2.0) == ([], [], []):
                    # Timeout reached: drain any pending outbox records as catch-up
                    process_pending_events(syncer, limit=50)
                else:
                    conn.poll()
                    while conn.notifies:
                        notify = conn.notifies.pop(0)
                        logger.debug(f"[CDC EVENT] Received notification: {notify.payload}")
                        # Immediately drain pending events
                        count = process_pending_events(syncer, limit=50)
                        if count > 0:
                            logger.info(f"[CDC SYNC] Real-time mirrored {count} change event(s) to Neo4j graph.")

        except Exception as e:
            logger.warning(f"[CDC WORKER] Connection error in CDC listener: {e}. Retrying in 5 seconds...")
            time.sleep(5.0)

    syncer.close()
    logger.info("[CDC WORKER] Shutdown complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    start_cdc_worker()
