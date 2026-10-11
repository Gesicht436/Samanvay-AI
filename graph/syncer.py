"""
Neo4j Graph Synchronization Engine for Samanvay-AI.

Provides real-time transactional synchronization (CDC) and manual property updates
conforming to the unified Dataset 1 Knowledge Graph structure:
(:Item) -> [:HAS_ITEM_TYPE] -> (:ItemType) -> [:HAS_ITEM] -> (:InventoryItem)
    ├── [:HAS_STOCK_INFO]   -> (:StockInfo)
    ├── [:STORED_AT]        -> (:Location) -> [:IN_STATE] -> (:State)
    ├── [:ORDERED_BY]       -> (:PurchaseOrder) -> [:PART_OF_TENDER] -> (:CPPPTender)
    ├── [:OPERATED_BY]      -> (:CPSE)
    └── [:HAS_SPECIFICATION]-> (:MaterialSpecification)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Sequence

from neo4j import GraphDatabase

from backend.app.core.config import get_neo4j_config
from graph.seed_graph import extract_item_type, validate_cpse_name

logger = logging.getLogger("samanvay.graph.syncer")

def _get_neo4j_config() -> tuple[str, str, str, dict]:
    """Dynamic delegation to consolidated get_neo4j_config helper."""
    return get_neo4j_config()



class _ClearSentinel:
    """Sentinel value used to explicitly clear / remove a property from a graph node."""

    def __repr__(self) -> str:
        return "CLEAR"


CLEAR = _ClearSentinel()


class Neo4jSyncer:
    """Synchronizes relational database transactions (CDC) and manual updates into Neo4j."""

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        c_uri, c_user, c_pwd, c_kwargs = _get_neo4j_config()
        self.uri = uri or c_uri
        self.user = user or c_user
        self.password = password or c_pwd
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
            **c_kwargs,
        )

    def close(self):
        if self.driver:
            self.driver.close()

    # ---------------------------------------------------------
    # 1. Update Existing Item & Stock Info
    # ---------------------------------------------------------
    def update_item(
        self,
        sku_code: str,
        quantity: Optional[Any] = None,
        unit_cost_inr: Optional[Any] = None,
        days_idle: Optional[Any] = None,
        heat_no: Optional[Any] = None,
        nominal_bore_mm: Optional[Any] = None,
        pressure_rating_bar: Optional[Any] = None,
        make_in_india_class: Optional[Any] = None,
        local_content_percentage: Optional[Any] = None,
        clear_fields: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Updates specific attributes of an existing InventoryItem and its StockInfo node.

        Partial Update Semantics
        ------------------------
        1. Omitted / None: The property is left strictly unchanged. Existing values
           are preserved and never cleared or overwritten unintentionally.
        2. Valid Value: The property is updated to the newly supplied value.
        3. CLEAR / clear_fields: The property is explicitly removed from the node
           via Cypher REMOVE (e.g. `heat_no=CLEAR` or `clear_fields=["heat_no"]`).
        4. Dependency-free: Uses standard Cypher SET and REMOVE clauses without
           requiring APOC plugins.
        """
        if not sku_code:
            raise ValueError("sku_code is required for update_item.")

        clear_set = set(clear_fields or [])

        # Categorize known properties into item vs stock
        stock_prop_names = {"quantity", "unit_cost_inr", "days_idle"}

        # Collect raw incoming arguments
        candidate_props: Dict[str, Any] = {
            "quantity": quantity,
            "unit_cost_inr": unit_cost_inr,
            "days_idle": days_idle,
            "heat_no": heat_no,
            "nominal_bore_mm": nominal_bore_mm,
            "pressure_rating_bar": pressure_rating_bar,
            "make_in_india_class": make_in_india_class,
            "local_content_percentage": local_content_percentage,
        }
        candidate_props.update(kwargs)

        item_set: Dict[str, Any] = {}
        item_remove: List[str] = []
        stock_set: Dict[str, Any] = {}
        stock_remove: List[str] = []

        for prop_name, val in candidate_props.items():
            is_stock = prop_name in stock_prop_names
            should_clear = (val is CLEAR) or (prop_name in clear_set)

            if should_clear:
                if is_stock:
                    stock_remove.append(prop_name)
                else:
                    item_remove.append(prop_name)
            elif val is not None:
                if is_stock:
                    stock_set[prop_name] = val
                else:
                    item_set[prop_name] = val
            # If val is None and not in clear_set, leave completely unchanged (do nothing)

        # Also handle any extra properties listed in clear_fields that were not in candidate_props
        for prop_name in clear_set:
            if prop_name not in candidate_props:
                if prop_name in stock_prop_names:
                    if prop_name not in stock_remove:
                        stock_remove.append(prop_name)
                else:
                    if prop_name not in item_remove:
                        item_remove.append(prop_name)

        # Build Cypher query clauses
        query_lines = [
            "MATCH (item:InventoryItem {sku_code: $sku_code})",
            "OPTIONAL MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)",
        ]
        params: Dict[str, Any] = {"sku_code": sku_code}

        if item_set:
            set_parts = []
            for p, val in item_set.items():
                param_key = f"set_item_{p}"
                params[param_key] = val
                set_parts.append(f"item.{p} = ${param_key}")
            query_lines.append("SET " + ", ".join(set_parts))

        if item_remove:
            remove_parts = [f"item.{p}" for p in item_remove]
            query_lines.append("REMOVE " + ", ".join(remove_parts))

        if stock_set:
            set_parts = []
            for p, val in stock_set.items():
                param_key = f"set_stock_{p}"
                params[param_key] = val
                set_parts.append(f"stock.{p} = ${param_key}")
            query_lines.append("SET " + ", ".join(set_parts))

        if stock_remove:
            remove_parts = [f"stock.{p}" for p in stock_remove]
            query_lines.append("REMOVE " + ", ".join(remove_parts))

        query_lines.append("RETURN properties(item) AS item, properties(stock) AS stock")
        query = "\n".join(query_lines)

        with self.driver.session() as session:
            result = session.run(query, params)
            rec = result.single()
            if rec is None:
                raise ValueError(f"InventoryItem with SKU '{sku_code}' not found.")
            return dict(rec)

    # ---------------------------------------------------------
    # 2. Batch Sync Inventory (used by CDC Manager)
    # ---------------------------------------------------------
    def batch_sync_inventory(self, items: List[Dict[str, Any]], batch_size: int = 500) -> int:
        """Upserts a list of inventory items into the unified graph."""
        if not items:
            return 0

        query = """
        UNWIND $rows AS row

        MERGE (root:Item {name: "Item"})

        MERGE (item_type:ItemType {name: row.item_type})
        MERGE (root)-[:HAS_ITEM_TYPE]->(item_type)

        MERGE (item:InventoryItem {sku_code: row.sku_code})
        SET item.heat_no = row.heat_no,
            item.nominal_bore_mm = row.nominal_bore_mm,
            item.pressure_rating_bar = row.pressure_rating_bar,
            item.make_in_india_class = row.make_in_india_class,
            item.local_content_percentage = row.local_content_percentage

        MERGE (item_type)-[:HAS_ITEM]->(item)

        MERGE (stock:StockInfo {sku_code: row.sku_code})
        SET stock.quantity = row.quantity,
            stock.unit_cost_inr = row.unit_cost_inr,
            stock.days_idle = row.days_idle

        MERGE (item)-[:HAS_STOCK_INFO]->(stock)

        MERGE (location:Location {name: row.depot_location})
        MERGE (state:State {name: row.location_state})
        MERGE (item)-[:STORED_AT]->(location)
        MERGE (location)-[:IN_STATE]->(state)

        MERGE (po:PurchaseOrder {po_no: row.po_no})
        MERGE (item)-[:ORDERED_BY]->(po)

        FOREACH (_ IN CASE WHEN row.cppp_tender_id IS NOT NULL AND trim(row.cppp_tender_id) <> '' THEN [1] ELSE [] END |
            MERGE (tender:CPPPTender {tender_id: row.cppp_tender_id})
            SET tender.tender_ref = row.cppp_tender_ref
            MERGE (po)-[:PART_OF_TENDER]->(tender)
        )

        MERGE (cpse:CPSE {name: row.cpse_name})
        MERGE (item)-[:OPERATED_BY]->(cpse)

        MERGE (spec:MaterialSpecification {sku_code: row.sku_code})
        SET spec.raw_description = row.raw_description,
            spec.standard = row.standard,
            spec.hsn_code = row.hsn_code,
            spec.mesc_code = row.mesc_code,
            spec.gem_category = row.gem_category,
            spec.gem_category_id = row.gem_category_id,
            spec.indian_standard = row.indian_standard,
            spec.oil_std_spec = row.oil_std_spec,
            spec.oil_material_code = row.oil_material_code

        MERGE (item)-[:HAS_SPECIFICATION]->(spec)
        """

        prepared = []
        for i in items:
            raw_desc = i.get("raw_description") or i.get("description") or ""
            it = i.get("item_type") or extract_item_type(raw_desc)
            loc = i.get("depot_location") or i.get("depot_id") or "Main Depot"
            state = i.get("location_state") or i.get("state") or "Assam"
            raw_cpse = i.get("cpse_name") or i.get("cpse")
            cpse = validate_cpse_name(raw_cpse)
            po = i.get("po_no") or "PO-GENERIC"

            prepared.append({
                "sku_code": i.get("sku_code", ""),
                "item_type": it,
                "heat_no": i.get("heat_no"),
                "nominal_bore_mm": float(i.get("nominal_bore_mm") or i.get("size_nb_mm") or 0.0),
                "pressure_rating_bar": float(i.get("pressure_rating_bar") or 0.0),
                "make_in_india_class": i.get("make_in_india_class", "Class-I"),
                "local_content_percentage": float(i.get("local_content_percentage") or 75.0),
                "quantity": int(i.get("quantity") or 0),
                "unit_cost_inr": float(i.get("unit_cost_inr") or 0.0),
                "days_idle": int(i.get("days_idle") or 0),
                "depot_location": loc,
                "location_state": state,
                "po_no": po,
                "cppp_tender_id": i.get("cppp_tender_id"),
                "cppp_tender_ref": i.get("cppp_tender_ref"),
                "cpse_name": cpse,
                "raw_description": raw_desc,
                "standard": i.get("standard"),
                "hsn_code": i.get("hsn_code"),
                "mesc_code": i.get("mesc_code"),
                "gem_category": i.get("gem_category"),
                "gem_category_id": i.get("gem_category_id"),
                "indian_standard": i.get("indian_standard"),
                "oil_std_spec": i.get("oil_std_spec"),
                "oil_material_code": i.get("oil_material_code"),
            })

        total = len(prepared)
        with self.driver.session() as session:
            for start in range(0, total, batch_size):
                chunk = prepared[start:start + batch_size]
                session.run(query, rows=chunk).consume()

        return total

    # ---------------------------------------------------------
    # 3. Sync Requisition Node
    # ---------------------------------------------------------
    def sync_requisition(self, req: Dict[str, Any]):
        """Persists or updates an inter-CPSE requisition node."""
        query = """
        MERGE (r:Requisition {requisition_id: $requisition_id})
        SET r.source_cpse = $source_cpse,
            r.target_cpse = $target_cpse,
            r.source_depot = $source_depot,
            r.target_depot = $target_depot,
            r.sku_code = $sku_code,
            r.required_qty = $required_qty,
            r.unit_cost_inr = $unit_cost_inr,
            r.total_value_inr = $total_value_inr,
            r.status = $status,
            r.urgency_level = $urgency_level,
            r.justification = $justification,
            r.requested_by = $requested_by,
            r.approved_by = $approved_by,
            r.audit_hash = $audit_hash

        WITH r
        OPTIONAL MATCH (item:InventoryItem {sku_code: r.sku_code})
        FOREACH (_ IN CASE WHEN item IS NOT NULL THEN [1] ELSE [] END |
            MERGE (r)-[:REQUESTS_ITEM]->(item)
        )
        """
        with self.driver.session() as session:
            session.run(query, **req).consume()

    # ---------------------------------------------------------
    # 4. Delete Inventory Item with Orphan Cleanup
    # ---------------------------------------------------------
    def delete_inventory_item(self, sku_code: str) -> None:
        """
        Deletes an InventoryItem and its exclusively-owned leaf nodes
        (StockInfo, MaterialSpecification), then safely cleans up
        orphaned PurchaseOrders and CPPPTenders.

        Safety guarantees
        -----------------
        - A PurchaseOrder is deleted **only** when no other InventoryItem
          still references it via [:ORDERED_BY].
        - A CPPPTender is deleted **only** when no PurchaseOrder still
          references it via [:PART_OF_TENDER].
        - All three steps run inside a single writable transaction to
          prevent partial states.
        """
        # Step 1: collect the PO references before the item is gone.
        # Step 2: delete the item and its exclusive leaf nodes.
        # Step 3: delete any now-orphaned POs (no remaining [:ORDERED_BY] edges).
        # Step 4: delete any now-orphaned Tenders (no remaining [:PART_OF_TENDER] edges).
        query = """
        // 1. Collect the PurchaseOrder(s) the item pointed to
        OPTIONAL MATCH (item:InventoryItem {sku_code: $sku_code})-[:ORDERED_BY]->(po:PurchaseOrder)
        WITH item, collect(po) AS pos

        // 2. Delete item and its exclusively-owned leaf nodes
        OPTIONAL MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
        OPTIONAL MATCH (item)-[:HAS_SPECIFICATION]->(spec:MaterialSpecification)
        DETACH DELETE item, stock, spec

        // 3. For each collected PO: delete it if no InventoryItem still references it
        WITH pos
        UNWIND pos AS po
        OPTIONAL MATCH (other_item:InventoryItem)-[:ORDERED_BY]->(po)
        WITH po, count(other_item) AS still_referenced
        // 3a. If this PO is now unreferenced, also collect its tenders before deletion
        OPTIONAL MATCH (po)-[:PART_OF_TENDER]->(tender:CPPPTender)
            WHERE still_referenced = 0
        WITH po, tender, still_referenced
        FOREACH (_ IN CASE WHEN still_referenced = 0 THEN [1] ELSE [] END |
            DETACH DELETE po
        )

        // 4. Delete the tender only when no PurchaseOrder references it any more
        WITH collect(tender) AS tenders
        UNWIND tenders AS t
        OPTIONAL MATCH (remaining_po:PurchaseOrder)-[:PART_OF_TENDER]->(t)
        WITH t, count(remaining_po) AS po_count
        FOREACH (_ IN CASE WHEN po_count = 0 THEN [1] ELSE [] END |
            DETACH DELETE t
        )
        """
        with self.driver.session() as session:
            session.run(query, sku_code=sku_code).consume()

    # ---------------------------------------------------------
    # 5. Outbox CDC Event Dispatcher
    # ---------------------------------------------------------
    def sync_event(self, table_name: str, operation: str, payload: Dict[str, Any]):
        """Dispatches PostgreSQL transactional CDC events to Neo4j."""
        if table_name.lower() in ("inventory_items", "inventoryitem"):
            sku = payload.get("sku_code")
            if not sku:
                return

            if operation.upper() == "DELETE":
                self.delete_inventory_item(sku)
            else:
                self.batch_sync_inventory([payload])

        elif table_name.lower() in ("requisitions", "requisition"):
            if operation.upper() == "DELETE":
                req_id = payload.get("requisition_id")
                with self.driver.session() as session:
                    session.run("MATCH (r:Requisition {requisition_id: $id}) DETACH DELETE r", id=req_id).consume()
            else:
                self.sync_requisition(payload)


# Backward-compatible alias
GraphSyncer = Neo4jSyncer


if __name__ == "__main__":
    syncer = Neo4jSyncer()
    try:
        res = syncer.update_item(sku_code="OIL-STU-00001", days_idle=75)
        print("Updated:", res)
    finally:
        syncer.close()
