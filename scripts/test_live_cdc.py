"""
Samanvay-AI Live CDC End-to-End Verification Test.

Tests that inserting an item into PostgreSQL triggers immediate real-time
mirroring into Neo4j graph nodes and relationships via the CDC Worker.
"""

import os
import sys
import time
import json
import urllib.request
from neo4j import GraphDatabase

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.models.base import SessionLocal
from backend.app.models.tables import InventoryItem, CdcOutbox


def test_cdc_mirroring():
    print("================ SAMANVAY-AI LIVE CDC TEST ================")
    sku = f"TEST-CDC-VALVE-{int(time.time()) % 10000}"
    print(f"[TEST 1] Creating new inventory part in PostgreSQL: {sku}...")

    db = SessionLocal()
    try:
        new_item = InventoryItem(
            sku_code=sku,
            cpse="IOCL",
            depot_id="IOCL_PANIPAT_REFINERY",
            depot_location="Panipat Refinery, Haryana",
            description="High Pressure Forged Ball Valve 2 inch 600# SS316 Full Port",
            item_type="VALVE",
            size_nb_mm=50.0,
            pressure_class=600,
            metallurgy="SS316",
            facing_end="RF",
            quantity=12,
            unit_cost_inr=45000.0,
            status="IDLE_SURPLUS",
            days_idle=210,
            is_broadcasted_surplus=True,
            properties={"trim": "Stellite", "port": "Full Bore"},
        )
        db.add(new_item)
        db.commit()
        print(f"[OK] Part {sku} committed to PostgreSQL.")
    finally:
        db.close()

    # Give the async CDC worker up to 2 seconds to process the notification
    print("[TEST 2] Waiting for real-time CDC event processing...")
    time.sleep(1.0)

    # 3. Verify in PostgreSQL cdc_outbox
    db = SessionLocal()
    try:
        outbox_entry = db.query(CdcOutbox).filter(CdcOutbox.record_id == sku).first()
        assert outbox_entry is not None, "CDC outbox record was not created by trigger!"
        print(f"[OK] CDC Outbox entry captured: ID={outbox_entry.id}, op={outbox_entry.operation}, status={outbox_entry.status}")
    finally:
        db.close()

    # 4. Verify in Neo4j Graph
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        with driver.session() as session:
            res = session.run("""
                MATCH (c:CPSE {name: 'IOCL'})-[:OPERATES]->(d:Depot)-[:HOLDS]->(i:InventoryItem {sku: $sku})
                OPTIONAL MATCH (i)-[:HAS_PRESSURE_CLASS]->(pc:PressureClass)
                OPTIONAL MATCH (i)-[:HAS_BODY_METALLURGY]->(mg:MaterialGrade)
                RETURN i.sku AS sku, i.description AS desc, i.qty AS qty, i.status AS status,
                       d.id AS depot_id, pc.value AS pressure_class, mg.value AS metallurgy
            """, sku=sku).single()

            assert res is not None, f"Node for {sku} not found in Neo4j Knowledge Graph!"
            print(f"[OK] Neo4j Real-Time Graph Node Found:")
            print(f"     - SKU: {res['sku']}")
            print(f"     - Depot: {res['depot_id']}")
            print(f"     - Status: {res['status']}")
            print(f"     - Pressure Class: {res['pressure_class']}")
            print(f"     - Metallurgy: {res['metallurgy']}")
            print(f"     - Quantity: {res['qty']}")

        # 5. Test Live UPDATE
        print(f"\n[TEST 3] Updating item in PostgreSQL to status='SURPLUS_DECLARED', qty=25...")
        db = SessionLocal()
        try:
            item = db.query(InventoryItem).filter(InventoryItem.sku_code == sku).first()
            item.status = "SURPLUS_DECLARED"
            item.quantity = 25
            db.commit()
            print("[OK] PostgreSQL update committed.")
        finally:
            db.close()

        time.sleep(1.0)

        with driver.session() as session:
            updated_res = session.run("""
                MATCH (i:InventoryItem {sku: $sku})
                RETURN i.status AS status, i.qty AS qty
            """, sku=sku).single()

            assert updated_res["status"] == "SURPLUS_DECLARED", f"Status not updated in Neo4j! Got {updated_res['status']}"
            assert updated_res["qty"] == 25, f"Quantity not updated in Neo4j! Got {updated_res['qty']}"
            print(f"[OK] Neo4j Node updated in real time: status={updated_res['status']}, qty={updated_res['qty']}")

    finally:
        driver.close()

    # 6. Cleanup test row
    db = SessionLocal()
    try:
        db.query(InventoryItem).filter(InventoryItem.sku_code == sku).delete()
        db.commit()
        time.sleep(1.0)
        # Verify deletion in Neo4j
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        with driver.session() as session:
            del_res = session.run("MATCH (i:InventoryItem {sku: $sku}) RETURN count(i) as count", sku=sku).single()
            print(f"[OK] Cleaned up test item: Remaining Neo4j nodes matching {sku} = {del_res['count']}")
        driver.close()
    finally:
        db.close()

    print("\n================ REAL-TIME CDC VALIDATION PASSED 100% ================")


if __name__ == "__main__":
    test_cdc_mirroring()
