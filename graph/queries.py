"""
Graph Query Engine for Samanvay-AI Neo4j Knowledge Graph.

Executes traversal queries against the unified Dataset 1 architecture:
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
from typing import Any, Dict, List, Optional

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    GraphDatabase = None
    NEO4J_AVAILABLE = False

logger = logging.getLogger("samanvay.graph.queries")


def _get_neo4j_config() -> tuple[str, str, str]:
    uri = None
    user = None
    password = None

    try:
        from backend.app.core.config import settings
        uri = getattr(settings, "neo4j_uri", None) or getattr(settings, "NEO4J_URI", None)
        user = getattr(settings, "neo4j_user", None) or getattr(settings, "NEO4J_USER", None)
        password = getattr(settings, "neo4j_password", None) or getattr(settings, "NEO4J_PASSWORD", None)
    except Exception:
        pass

    if not uri:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    if not user:
        user = os.getenv("NEO4J_USER", "neo4j")
    if not password:
        password = os.getenv("NEO4J_PASSWORD", "samanvay_graph")

    return str(uri), str(user), str(password)


class GraphQuerier:
    """Provides structured Cypher querying across all unified graph nodes and relationships."""

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        self.driver = None
        if not NEO4J_AVAILABLE:
            logger.warning("neo4j python package is not available.")
            return

        c_uri, c_user, c_pwd = _get_neo4j_config()
        self.uri = uri or c_uri
        self.user = user or c_user
        self.password = password or c_pwd

        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    # ---------------------------------------------------------
    # 1. Complete Item by SKU Subgraph
    # ---------------------------------------------------------
    def get_item_by_sku(self, sku_code: str) -> Dict[str, Any]:
        """
        Retrieves complete unified subgraph for a given SKU:
        ItemType, StockInfo, Location, State, PurchaseOrder, CPPPTender, CPSE, MaterialSpecification.
        """
        if not self.driver:
            return {}

        query = """
        MATCH (item:InventoryItem {sku_code: $sku_code})
        OPTIONAL MATCH (root:Item)-[:HAS_ITEM_TYPE]->(item_type:ItemType)-[:HAS_ITEM]->(item)
        OPTIONAL MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
        OPTIONAL MATCH (item)-[:STORED_AT]->(location:Location)
        OPTIONAL MATCH (location)-[:IN_STATE]->(state:State)
        OPTIONAL MATCH (item)-[:ORDERED_BY]->(po:PurchaseOrder)
        OPTIONAL MATCH (po)-[:PART_OF_TENDER]->(tender:CPPPTender)
        OPTIONAL MATCH (item)-[:OPERATED_BY]->(cpse:CPSE)
        OPTIONAL MATCH (item)-[:HAS_SPECIFICATION]->(spec:MaterialSpecification)

        RETURN
            root.name AS root_item,
            item_type.name AS item_type,
            properties(item) AS item,
            properties(stock) AS stock,
            location.name AS location,
            state.name AS state,
            po.po_no AS po_no,
            tender.tender_id AS tender_id,
            tender.tender_ref AS tender_ref,
            cpse.name AS cpse,
            properties(spec) AS specification
        """

        with self.driver.session() as session:
            record = session.run(query, sku_code=sku_code).single()
            if record:
                return dict(record)
        return {}

    # ---------------------------------------------------------
    # 2. Get Items by ItemType
    # ---------------------------------------------------------
    def get_items_by_item_type(self, item_type_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Finds all InventoryItems under a specific ItemType."""
        if not self.driver:
            return []

        query = """
        MATCH (item_type:ItemType {name: $item_type_name})-[:HAS_ITEM]->(item:InventoryItem)
        OPTIONAL MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
        OPTIONAL MATCH (item)-[:STORED_AT]->(loc:Location)
        OPTIONAL MATCH (item)-[:OPERATED_BY]->(cpse:CPSE)
        RETURN
            item.sku_code AS sku_code,
            item.nominal_bore_mm AS nominal_bore_mm,
            item.pressure_rating_bar AS pressure_rating_bar,
            item.make_in_india_class AS make_in_india_class,
            stock.quantity AS quantity,
            stock.unit_cost_inr AS unit_cost_inr,
            stock.days_idle AS days_idle,
            loc.name AS location,
            cpse.name AS cpse
        ORDER BY item.sku_code ASC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, item_type_name=item_type_name, limit=limit)
            return [dict(rec) for rec in result]

    # ---------------------------------------------------------
    # 3. Get Items by State
    # ---------------------------------------------------------
    def get_items_by_state(self, state_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves items stored at depots within a designated Indian State."""
        if not self.driver:
            return []

        query = """
        MATCH (item:InventoryItem)-[:STORED_AT]->(loc:Location)-[:IN_STATE]->(state:State {name: $state_name})
        OPTIONAL MATCH (item)<-[:HAS_ITEM]-(it:ItemType)
        OPTIONAL MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
        OPTIONAL MATCH (item)-[:OPERATED_BY]->(cpse:CPSE)
        RETURN
            item.sku_code AS sku_code,
            it.name AS item_type,
            loc.name AS location,
            state.name AS state,
            cpse.name AS cpse,
            stock.quantity AS quantity,
            stock.days_idle AS days_idle
        ORDER BY item.sku_code ASC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, state_name=state_name, limit=limit)
            return [dict(rec) for rec in result]

    # ---------------------------------------------------------
    # 4. Get Items by Location
    # ---------------------------------------------------------
    def get_items_by_location(self, location_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves items stored at a specific CPSE depot/location."""
        if not self.driver:
            return []

        query = """
        MATCH (item:InventoryItem)-[:STORED_AT]->(loc:Location {name: $location_name})
        OPTIONAL MATCH (item)<-[:HAS_ITEM]-(it:ItemType)
        OPTIONAL MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
        OPTIONAL MATCH (item)-[:OPERATED_BY]->(cpse:CPSE)
        RETURN
            item.sku_code AS sku_code,
            it.name AS item_type,
            loc.name AS location,
            cpse.name AS cpse,
            stock.quantity AS quantity,
            stock.days_idle AS days_idle
        ORDER BY item.sku_code ASC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, location_name=location_name, limit=limit)
            return [dict(rec) for rec in result]

    # ---------------------------------------------------------
    # 5. Get Surplus by CPSE
    # ---------------------------------------------------------
    def get_cpse_surplus(self, cpse_name: str, min_days_idle: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns surplus equipment for a given CPSE ordered by days idle."""
        if not self.driver:
            return []

        query = """
        MATCH (item:InventoryItem)-[:OPERATED_BY]->(cpse:CPSE {name: $cpse_name})
        OPTIONAL MATCH (item)<-[:HAS_ITEM]-(it:ItemType)
        OPTIONAL MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
        OPTIONAL MATCH (item)-[:STORED_AT]->(loc:Location)
        WHERE stock.days_idle >= $min_days_idle
        RETURN
            item.sku_code AS sku_code,
            it.name AS item_type,
            cpse.name AS cpse,
            loc.name AS location,
            stock.quantity AS quantity,
            stock.days_idle AS days_idle,
            stock.unit_cost_inr AS unit_cost_inr
        ORDER BY stock.days_idle DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, cpse_name=cpse_name, min_days_idle=min_days_idle, limit=limit)
            return [dict(rec) for rec in result]

    # ---------------------------------------------------------
    # 6. Get Idle Items
    # ---------------------------------------------------------
    def get_idle_items(self, min_days_idle: int = 90, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns non-moving/dormant items across all CPSEs."""
        if not self.driver:
            return []

        query = """
        MATCH (item:InventoryItem)-[:HAS_STOCK_INFO]->(stock:StockInfo)
        WHERE stock.days_idle >= $min_days_idle
        OPTIONAL MATCH (item)<-[:HAS_ITEM]-(it:ItemType)
        OPTIONAL MATCH (item)-[:STORED_AT]->(loc:Location)
        OPTIONAL MATCH (item)-[:OPERATED_BY]->(cpse:CPSE)
        RETURN
            item.sku_code AS sku_code,
            it.name AS item_type,
            stock.days_idle AS days_idle,
            stock.quantity AS quantity,
            stock.unit_cost_inr AS unit_cost_inr,
            loc.name AS location,
            cpse.name AS cpse
        ORDER BY stock.days_idle DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, min_days_idle=min_days_idle, limit=limit)
            return [dict(rec) for rec in result]

    # ---------------------------------------------------------
    # 7. Get Material Specification
    # ---------------------------------------------------------
    def get_item_specification(self, sku_code: str) -> Dict[str, Any]:
        """Fetches the consolidated MaterialSpecification node for an item."""
        if not self.driver:
            return {}

        query = """
        MATCH (item:InventoryItem {sku_code: $sku_code})-[:HAS_SPECIFICATION]->(spec:MaterialSpecification)
        RETURN properties(spec) AS specification
        """

        with self.driver.session() as session:
            record = session.run(query, sku_code=sku_code).single()
            if record and record["specification"]:
                return dict(record["specification"])
        return {}

    # ---------------------------------------------------------
    # 8. Hierarchical Path (Item -> ItemType -> InventoryItem -> Branches)
    # ---------------------------------------------------------
    def get_item_hierarchy(self, sku_code: str) -> Dict[str, Any]:
        """Demonstrates top-down hierarchical traversal for visualization."""
        if not self.driver:
            return {}

        query = """
        MATCH (root:Item)-[:HAS_ITEM_TYPE]->(item_type:ItemType)-[:HAS_ITEM]->(item:InventoryItem {sku_code: $sku_code})
        OPTIONAL MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
        OPTIONAL MATCH (item)-[:STORED_AT]->(loc:Location)-[:IN_STATE]->(state:State)
        OPTIONAL MATCH (item)-[:ORDERED_BY]->(po:PurchaseOrder)
        OPTIONAL MATCH (po)-[:PART_OF_TENDER]->(tender:CPPPTender)
        OPTIONAL MATCH (item)-[:OPERATED_BY]->(cpse:CPSE)
        OPTIONAL MATCH (item)-[:HAS_SPECIFICATION]->(spec:MaterialSpecification)
        RETURN
            root.name AS root,
            item_type.name AS item_type,
            item.sku_code AS sku_code,
            properties(item) AS item_props,
            properties(stock) AS stock,
            loc.name AS location,
            state.name AS state,
            po.po_no AS po_no,
            tender.tender_id AS tender_id,
            cpse.name AS cpse,
            properties(spec) AS specification
        """

        with self.driver.session() as session:
            record = session.run(query, sku_code=sku_code).single()
            if record:
                return dict(record)
        return {}

    # ---------------------------------------------------------
    # 9. All Item Types with Counts
    # ---------------------------------------------------------
    def get_all_item_types(self) -> List[Dict[str, Any]]:
        """Returns all ItemType categories with their inventory counts."""
        if not self.driver:
            return []

        query = """
        MATCH (root:Item)-[:HAS_ITEM_TYPE]->(it:ItemType)
        OPTIONAL MATCH (it)-[:HAS_ITEM]->(item:InventoryItem)
        RETURN
            it.name AS item_type,
            count(item) AS count
        ORDER BY count DESC
        """

        with self.driver.session() as session:
            result = session.run(query)
            return [dict(rec) for rec in result]

    # ---------------------------------------------------------
    # 10. Graph Topology Summary
    # ---------------------------------------------------------
    def get_graph_topology(self) -> Dict[str, Any]:
        """Provides node and relationship counts verifying the unified graph structure."""
        if not self.driver:
            return {}

        query = """
        CALL apoc.meta.stats() YIELD nodeCount, relCount, labels, relTypes
        RETURN nodeCount, relCount, labels, relTypes
        """

        # Fallback if APOC is not enabled
        fallback_query = """
        MATCH (n)
        RETURN count(n) AS total_nodes
        """

        with self.driver.session() as session:
            try:
                rec = session.run(query).single()
                if rec:
                    return {
                        "total_nodes": rec["nodeCount"],
                        "total_relationships": rec["relCount"],
                        "node_counts": dict(rec["labels"]),
                        "rel_types": dict(rec["relTypes"]),
                    }
            except Exception:
                pass

            total_nodes = session.run(fallback_query).single()["total_nodes"]
            total_rels = session.run("MATCH ()-[r]->() RETURN count(r) AS total_rels").single()["total_rels"]
            labels_rec = session.run("CALL db.labels() YIELD label RETURN label").data()

            node_counts = {}
            for l in labels_rec:
                lbl = l["label"]
                cnt = session.run(f"MATCH (n:`{lbl}`) RETURN count(n) AS c").single()["c"]
                node_counts[lbl] = cnt

            return {
                "total_nodes": total_nodes,
                "total_relationships": total_rels,
                "node_counts": node_counts,
            }
