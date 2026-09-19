"""
Samanvay-AI Neo4j Graph Synchronization Engine.

Translates PostgreSQL relational change events into Cypher property graph updates
in real-time, maintaining the Sovereign Multi-CPSE Star Graph and transit corridors.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from neo4j import GraphDatabase
from graph.logistics import DEPOT_COORDINATES

logger = logging.getLogger("samanvay.graph_syncer")


class Neo4jSyncer:
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        if not uri:
            try:
                from backend.app.core.config import settings
                self.uri = settings.neo4j_uri
                self.user = settings.neo4j_user
                self.password = settings.neo4j_password
            except Exception:
                self.uri = "bolt://localhost:7687"
                self.user = "neo4j"
                self.password = "samanvay_graph"
        else:
            self.uri = uri
            self.user = user or "neo4j"
            self.password = password or "samanvay_graph"

        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.ensure_constraints()

    def close(self):
        if self.driver:
            self.driver.close()

    def ensure_constraints(self):
        """Creates unique property constraints and indexes on nodes."""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:CPSE) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Depot) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:InventoryItem) REQUIRE i.sku IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Size) REQUIRE s.value IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:PressureClass) REQUIRE p.value IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:MaterialGrade) REQUIRE m.value IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Requisition) REQUIRE r.id IS UNIQUE",
        ]
        with self.driver.session() as session:
            for query in constraints:
                try:
                    session.run(query)
                except Exception as e:
                    logger.debug(f"Constraint notice ({query}): {e}")

    def sync_inventory_item(self, item: Dict[str, Any]):
        """Synchronizes a single inventory item into Neo4j graph nodes and relationships."""
        sku_code = item.get("sku_code")
        if not sku_code:
            return

        cpse = (item.get("cpse") or "IOCL").upper()
        depot_id = item.get("depot_id") or f"{cpse}_DEPOT"
        depot_loc = item.get("depot_location") or depot_id

        # Lookup coordinates
        matched_coord = None
        for name, coord in DEPOT_COORDINATES.items():
            if name.lower() in depot_loc.lower() or name.lower() in depot_id.lower():
                matched_coord = coord
                break
        if not matched_coord:
            matched_coord = (22.3217, 73.1384)

        lat, lon = matched_coord

        item_type = item.get("item_type") or "EQUIPMENT"
        size_val = None
        if item.get("size_nb_mm"):
            size_val = f"{float(item['size_nb_mm'])} mm"

        pressure_class_val = None
        if item.get("pressure_class"):
            pressure_class_val = f"{item['pressure_class']}#"

        metallurgy_val = item.get("metallurgy")
        facing_val = item.get("facing_end")
        qty = int(item.get("quantity") or 0)
        days_idle = int(item.get("days_idle") or 0)
        unit_cost = float(item.get("unit_cost_inr") or 0.0)
        total_val = float(item.get("total_value_inr") or (qty * unit_cost))
        status = item.get("status") or "TO_BE_CONSUMED"
        desc = item.get("description") or ""

        cypher = """
        // 1. CPSE and Depot
        MERGE (c:CPSE {name: $cpse})
        MERGE (d:Depot {id: $depot_id})
        ON CREATE SET d.name = $depot_loc, d.lat = $lat, d.lon = $lon
        ON MATCH SET d.name = $depot_loc, d.lat = $lat, d.lon = $lon
        MERGE (c)-[:OPERATES]->(d)

        // 2. Inventory Item
        MERGE (i:InventoryItem {sku: $sku_code})
        SET i.description = $desc,
            i.item_type = $item_type,
            i.qty = $qty,
            i.days_idle = $days_idle,
            i.status = $status,
            i.unit_cost_inr = $unit_cost,
            i.total_value_inr = $total_val,
            i.is_broadcasted_surplus = $is_broadcast,
            i.updated_at = datetime()

        // 3. Depot Holds Item & Item belongs to CPSE
        MERGE (d)-[:HOLDS]->(i)
        MERGE (i)-[:BELONGS_TO_CPSE]->(c)

        WITH i
        // 4. Property Star Relationships
        FOREACH (_ IN CASE WHEN $size_val IS NOT NULL THEN [1] ELSE [] END |
            MERGE (sz:Size {value: $size_val})
            MERGE (i)-[:HAS_SIZE]->(sz)
        )
        FOREACH (_ IN CASE WHEN $pressure_class_val IS NOT NULL THEN [1] ELSE [] END |
            MERGE (pc:PressureClass {value: $pressure_class_val})
            MERGE (i)-[:HAS_PRESSURE_CLASS]->(pc)
        )
        FOREACH (_ IN CASE WHEN $metallurgy_val IS NOT NULL THEN [1] ELSE [] END |
            MERGE (mg:MaterialGrade {value: $metallurgy_val})
            MERGE (i)-[:HAS_BODY_METALLURGY]->(mg)
        )
        """

        with self.driver.session() as session:
            session.run(
                cypher,
                cpse=cpse,
                depot_id=depot_id,
                depot_loc=depot_loc,
                lat=lat,
                lon=lon,
                sku_code=sku_code,
                desc=desc,
                item_type=item_type,
                qty=qty,
                days_idle=days_idle,
                status=status,
                unit_cost=unit_cost,
                total_val=total_val,
                is_broadcast=bool(item.get("is_broadcasted_surplus")),
                size_val=size_val,
                pressure_class_val=pressure_class_val,
                metallurgy_val=metallurgy_val,
            )

    def batch_sync_inventory(self, items: List[Dict[str, Any]], batch_size: int = 500):
        """High-throughput bulk ingestion using UNWIND Cypher batching."""
        for i in range(0, len(items), batch_size):
            chunk = items[i : i + batch_size]
            prepared = []
            for item in chunk:
                sku_code = item.get("sku_code")
                if not sku_code:
                    continue
                cpse = (item.get("cpse") or "IOCL").upper()
                depot_id = item.get("depot_id") or f"{cpse}_DEPOT"
                depot_loc = item.get("depot_location") or depot_id

                matched_coord = None
                for name, coord in DEPOT_COORDINATES.items():
                    if name.lower() in depot_loc.lower() or name.lower() in depot_id.lower():
                        matched_coord = coord
                        break
                if not matched_coord:
                    matched_coord = (22.3217, 73.1384)

                size_val = f"{float(item['size_nb_mm'])} mm" if item.get("size_nb_mm") else None
                pc_val = f"{item['pressure_class']}#" if item.get("pressure_class") else None
                qty = int(item.get("quantity") or 0)
                unit_cost = float(item.get("unit_cost_inr") or 0.0)

                prepared.append({
                    "sku_code": sku_code,
                    "cpse": cpse,
                    "depot_id": depot_id,
                    "depot_loc": depot_loc,
                    "lat": matched_coord[0],
                    "lon": matched_coord[1],
                    "desc": item.get("description") or "",
                    "item_type": item.get("item_type") or "EQUIPMENT",
                    "qty": qty,
                    "days_idle": int(item.get("days_idle") or 0),
                    "status": item.get("status") or "TO_BE_CONSUMED",
                    "unit_cost": unit_cost,
                    "total_val": float(item.get("total_value_inr") or (qty * unit_cost)),
                    "is_broadcast": bool(item.get("is_broadcasted_surplus")),
                    "size_val": size_val,
                    "pressure_class_val": pc_val,
                    "metallurgy_val": item.get("metallurgy"),
                })

            cypher = """
            UNWIND $batch AS row
            MERGE (c:CPSE {name: row.cpse})
            MERGE (d:Depot {id: row.depot_id})
            ON CREATE SET d.name = row.depot_loc, d.lat = row.lat, d.lon = row.lon
            MERGE (c)-[:OPERATES]->(d)

            MERGE (i:InventoryItem {sku: row.sku_code})
            SET i.description = row.desc,
                i.item_type = row.item_type,
                i.qty = row.qty,
                i.days_idle = row.days_idle,
                i.status = row.status,
                i.unit_cost_inr = row.unit_cost,
                i.total_value_inr = row.total_val,
                i.is_broadcasted_surplus = row.is_broadcast,
                i.updated_at = datetime()

            MERGE (d)-[:HOLDS]->(i)
            MERGE (i)-[:BELONGS_TO_CPSE]->(c)

            WITH i, row
            FOREACH (_ IN CASE WHEN row.size_val IS NOT NULL THEN [1] ELSE [] END |
                MERGE (sz:Size {value: row.size_val})
                MERGE (i)-[:HAS_SIZE]->(sz)
            )
            FOREACH (_ IN CASE WHEN row.pressure_class_val IS NOT NULL THEN [1] ELSE [] END |
                MERGE (pc:PressureClass {value: row.pressure_class_val})
                MERGE (i)-[:HAS_PRESSURE_CLASS]->(pc)
            )
            FOREACH (_ IN CASE WHEN row.metallurgy_val IS NOT NULL THEN [1] ELSE [] END |
                MERGE (mg:MaterialGrade {value: row.metallurgy_val})
                MERGE (i)-[:HAS_BODY_METALLURGY]->(mg)
            )
            """

            with self.driver.session() as session:
                session.run(cypher, batch=prepared)

    def sync_requisition(self, req: Dict[str, Any]):
        """Synchronizes an inter-CPSE requisition into Neo4j graph nodes and logistics flows."""
        req_id = req.get("requisition_id")
        if not req_id:
            return

        cypher = """
        MERGE (r:Requisition {id: $req_id})
        SET r.source_cpse = $src_cpse,
            r.target_cpse = $tgt_cpse,
            r.required_qty = $qty,
            r.unit_cost_inr = $unit_cost,
            r.total_value_inr = $total_val,
            r.status = $status,
            r.urgency_level = $urgency,
            r.justification = $justification,
            r.requested_by = $requested_by,
            r.approved_by = $approved_by,
            r.audit_hash = $audit_hash,
            r.updated_at = datetime()

        // Link with requested item
        WITH r
        OPTIONAL MATCH (i:InventoryItem {sku: $sku_code})
        FOREACH (_ IN CASE WHEN i IS NOT NULL THEN [1] ELSE [] END |
            MERGE (r)-[:REQUESTS_ITEM]->(i)
        )

        // Link with source & target depots
        WITH r
        OPTIONAL MATCH (src_d:Depot)
        WHERE src_d.id = $src_depot
           OR toLower($src_depot) CONTAINS toLower(src_d.name)
           OR toLower(src_d.name) CONTAINS toLower($src_depot)
           OR toLower($src_depot) CONTAINS toLower(split(src_d.name, ',')[0])
           OR toLower(src_d.name) CONTAINS toLower(split($src_depot, ',')[0])
        WITH r, src_d LIMIT 1
        FOREACH (_ IN CASE WHEN src_d IS NOT NULL THEN [1] ELSE [] END |
            MERGE (src_d)-[:DISPATCHES_REQUISITION]->(r)
        )

        WITH r
        OPTIONAL MATCH (tgt_d:Depot)
        WHERE tgt_d.id = $tgt_depot
           OR toLower($tgt_depot) CONTAINS toLower(tgt_d.name)
           OR toLower(tgt_d.name) CONTAINS toLower($tgt_depot)
           OR toLower($tgt_depot) CONTAINS toLower(split(tgt_d.name, ',')[0])
           OR toLower(tgt_d.name) CONTAINS toLower(split($tgt_depot, ',')[0])
        WITH r, tgt_d LIMIT 1
        FOREACH (_ IN CASE WHEN tgt_d IS NOT NULL THEN [1] ELSE [] END |
            MERGE (r)-[:DESTINED_FOR]->(tgt_d)
        )
        """

        with self.driver.session() as session:
            session.run(
                cypher,
                req_id=req_id,
                src_cpse=req.get("source_cpse") or "IOCL",
                tgt_cpse=req.get("target_cpse") or "ONGC",
                src_depot=req.get("source_depot") or "",
                tgt_depot=req.get("target_depot") or "",
                sku_code=req.get("sku_code") or "",
                qty=int(req.get("required_qty") or req.get("quantity") or 1),
                unit_cost=float(req.get("unit_cost_inr") or 0.0),
                total_val=float(req.get("total_value_inr") or 0.0),
                status=req.get("status") or "PENDING_APPROVAL",
                urgency=req.get("urgency_level") or "EMERGENCY",
                justification=req.get("justification") or "",
                requested_by=req.get("requested_by") or "",
                approved_by=req.get("approved_by") or "",
                audit_hash=req.get("audit_hash") or "",
            )

    def sync_event(self, table_name: str, op: str, payload: Dict[str, Any]):
        """Dispatches an outbox change event to the appropriate graph syncer handler."""
        if table_name == "inventory_items":
            if op in ("INSERT", "UPDATE"):
                self.sync_inventory_item(payload)
            elif op == "DELETE":
                sku = payload.get("sku_code")
                if sku:
                    with self.driver.session() as session:
                        session.run("MATCH (i:InventoryItem {sku: $sku}) DETACH DELETE i", sku=sku)
        elif table_name == "requisitions":
            if op in ("INSERT", "UPDATE"):
                self.sync_requisition(payload)
            elif op == "DELETE":
                req_id = payload.get("requisition_id")
                if req_id:
                    with self.driver.session() as session:
                        session.run("MATCH (r:Requisition {id: $req_id}) DETACH DELETE r", req_id=req_id)
