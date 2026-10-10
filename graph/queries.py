"""
Graph Query Engine for Samanvay-AI Neo4j Knowledge Graph.

Executes traversal queries against the approved unified Dataset 1 architecture:
(:Item) -> [:HAS_ITEM_TYPE] -> (:ItemType) -> [:HAS_ITEM] -> (:InventoryItem)
    ├── [:HAS_STOCK_INFO]   -> (:StockInfo)
    ├── [:STORED_AT]        -> (:Location) -> [:IN_STATE] -> (:State)
    ├── [:ORDERED_BY]       -> (:PurchaseOrder) -> [:PART_OF_TENDER] -> (:CPPPTender)
    ├── [:OPERATED_BY]      -> (:CPSE)
    └── [:HAS_SPECIFICATION]-> (:MaterialSpecification)

Enforces strict CPSE-scoped data isolation and attribute-level commercial privacy:
- In-tenant reads access full stock information (including unit_cost_inr) and procurement data.
- Cross-tenant reads require explicit authorization (allow_cross_cpse=True).
- Cross-tenant results strictly strip confidential commercial pricing and procurement identifiers.
- Compatibility search validates verified physical properties (nominal_bore_mm, pressure_rating_bar)
  with zero speculation or unverified description matching.
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


def _get_neo4j_config() -> tuple[str, str, str, Dict[str, Any]]:
    """
    Returns (uri, user, password, driver_kwargs).

    driver_kwargs contains supported neo4j-python-driver connection pool
    and timeout settings sourced from application config or environment
    variables. Credentials are never included in driver_kwargs.
    """
    uri = None
    user = None
    password = None
    driver_kwargs: Dict[str, Any] = {}

    try:
        from backend.app.core.config import settings
        uri = getattr(settings, "neo4j_uri", None) or getattr(settings, "NEO4J_URI", None)
        user = getattr(settings, "neo4j_user", None) or getattr(settings, "NEO4J_USER", None)
        password = getattr(settings, "neo4j_password", None) or getattr(settings, "NEO4J_PASSWORD", None)
        driver_kwargs = {
            "connection_timeout": settings.neo4j_connection_timeout,
            "max_connection_lifetime": settings.neo4j_max_connection_lifetime,
            "max_connection_pool_size": settings.neo4j_max_connection_pool_size,
            "connection_acquisition_timeout": settings.neo4j_connection_acquisition_timeout,
        }
    except Exception:
        # Fall back to env-var defaults if config module is unavailable
        driver_kwargs = {
            "connection_timeout": int(os.getenv("NEO4J_CONNECTION_TIMEOUT", "15")),
            "max_connection_lifetime": int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600")),
            "max_connection_pool_size": int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50")),
            "connection_acquisition_timeout": int(
                os.getenv("NEO4J_CONNECTION_ACQUISITION_TIMEOUT", "60")
            ),
        }

    if not uri:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    if not user:
        user = os.getenv("NEO4J_USER", "neo4j")
    if not password:
        password = os.getenv("NEO4J_PASSWORD", "samanvay_graph")

    return str(uri), str(user), str(password), driver_kwargs


class GraphQuerier:
    """Provides structured, CPSE-scoped Cypher querying across unified graph nodes and relationships."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        requesting_cpse: Optional[str] = None,
        allow_cross_cpse: bool = False,
    ):
        self.driver = None
        self.requesting_cpse = requesting_cpse.strip().upper() if requesting_cpse else None
        self.allow_cross_cpse = bool(allow_cross_cpse)

        if not NEO4J_AVAILABLE:
            logger.warning("neo4j python package is not available.")
            return

        c_uri, c_user, c_pwd, c_kwargs = _get_neo4j_config()
        self.uri = uri or c_uri
        self.user = user or c_user
        self.password = password or c_pwd

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                **c_kwargs,
            )
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    # ---------------------------------------------------------
    # Authentication & Privacy Enforcement Helpers
    # ---------------------------------------------------------
    def _resolve_auth(
        self,
        requesting_cpse: Optional[str] = None,
        allow_cross_cpse: Optional[bool] = None,
    ) -> tuple[Optional[str], bool]:
        """Resolves active requesting CPSE and explicit cross-CPSE authorization flag."""
        req = requesting_cpse.strip().upper() if requesting_cpse else self.requesting_cpse
        cross = self.allow_cross_cpse if allow_cross_cpse is None else bool(allow_cross_cpse)
        return req, cross

    @staticmethod
    def _strip_commercial_fields_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Strips restricted commercial pricing and procurement identifiers for cross-CPSE isolation.
        Ensures unit costs, purchase orders, and tenders are never leaked to external CPSEs.
        """
        data = dict(item_data)
        if "stock" in data and isinstance(data["stock"], dict):
            stock_copy = dict(data["stock"])
            stock_copy.pop("unit_cost_inr", None)
            data["stock"] = stock_copy
        data.pop("unit_cost_inr", None)
        data["po_no"] = None
        data["tender_id"] = None
        data["tender_ref"] = None
        return data

    @staticmethod
    def _strip_commercial_fields_summary(row: Dict[str, Any]) -> Dict[str, Any]:
        """Strips commercial prices from list/summary query rows."""
        d = dict(row)
        d.pop("unit_cost_inr", None)
        if "po_no" in d:
            d["po_no"] = None
        if "tender_id" in d:
            d["tender_id"] = None
        return d

    # ---------------------------------------------------------
    # 1. Complete Item by SKU Subgraph
    # ---------------------------------------------------------
    def get_item_by_sku(
        self,
        sku_code: str,
        requesting_cpse: Optional[str] = None,
        allow_cross_cpse: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves complete unified subgraph for a given SKU:
        ItemType, StockInfo, Location, State, PurchaseOrder, CPPPTender, CPSE, MaterialSpecification.

        Enforces CPSE data scoping:
        - If item belongs to requesting CPSE: full data is returned.
        - If item belongs to a different CPSE: requires allow_cross_cpse=True.
          When allowed, commercial prices and tender data are stripped.
        - If cross-CPSE is not authorized or requester is unspecified, raises PermissionError.
        """
        if not self.driver:
            return {}

        req_cpse, is_cross = self._resolve_auth(requesting_cpse, allow_cross_cpse)
        if not req_cpse and not is_cross:
            raise PermissionError(
                "Access denied: A requesting CPSE or explicit cross-CPSE authorization is required. "
                "A SKU alone does not grant access to inventory."
            )

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
            if not record:
                return {}

            data = dict(record)
            item_cpse = data.get("cpse")

            if req_cpse and item_cpse and item_cpse != req_cpse:
                if not is_cross:
                    raise PermissionError(
                        f"Access denied: Requesting CPSE '{req_cpse}' is not authorized to access "
                        f"inventory item '{sku_code}' owned by '{item_cpse}'. Explicit cross-CPSE authorization required."
                    )
                data = self._strip_commercial_fields_item(data)
            elif not req_cpse and is_cross:
                data = self._strip_commercial_fields_item(data)

            return data

    # ---------------------------------------------------------
    # 2. Get Items by ItemType
    # ---------------------------------------------------------
    def get_items_by_item_type(
        self,
        item_type_name: str,
        limit: int = 50,
        requesting_cpse: Optional[str] = None,
        allow_cross_cpse: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Finds InventoryItems under a specific ItemType, scoped to authorized CPSE."""
        if not self.driver:
            return []

        req_cpse, is_cross = self._resolve_auth(requesting_cpse, allow_cross_cpse)
        if not req_cpse and not is_cross:
            raise PermissionError(
                "Access denied: A requesting CPSE or explicit cross-CPSE authorization is required."
            )

        if not is_cross:
            query = """
            MATCH (item_type:ItemType {name: $item_type_name})-[:HAS_ITEM]->(item:InventoryItem)
            MATCH (item)-[:OPERATED_BY]->(cpse:CPSE {name: $requesting_cpse})
            OPTIONAL MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
            OPTIONAL MATCH (item)-[:STORED_AT]->(loc:Location)
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
            params = {"item_type_name": item_type_name, "requesting_cpse": req_cpse, "limit": limit}
        else:
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
            params = {"item_type_name": item_type_name, "limit": limit}

        with self.driver.session() as session:
            result = session.run(query, **params)
            rows = []
            for rec in result:
                d = dict(rec)
                if (req_cpse and d.get("cpse") != req_cpse) or (not req_cpse and is_cross):
                    d = self._strip_commercial_fields_summary(d)
                rows.append(d)
            return rows

    # ---------------------------------------------------------
    # 3. Get Items by State
    # ---------------------------------------------------------
    def get_items_by_state(
        self,
        state_name: str,
        limit: int = 50,
        requesting_cpse: Optional[str] = None,
        allow_cross_cpse: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves items stored at depots within a designated Indian State."""
        if not self.driver:
            return []

        req_cpse, is_cross = self._resolve_auth(requesting_cpse, allow_cross_cpse)
        if not req_cpse and not is_cross:
            raise PermissionError(
                "Access denied: A requesting CPSE or explicit cross-CPSE authorization is required."
            )

        if not is_cross:
            query = """
            MATCH (item:InventoryItem)-[:STORED_AT]->(loc:Location)-[:IN_STATE]->(state:State {name: $state_name})
            MATCH (item)-[:OPERATED_BY]->(cpse:CPSE {name: $requesting_cpse})
            OPTIONAL MATCH (item)<-[:HAS_ITEM]-(it:ItemType)
            OPTIONAL MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
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
            params = {"state_name": state_name, "requesting_cpse": req_cpse, "limit": limit}
        else:
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
            params = {"state_name": state_name, "limit": limit}

        with self.driver.session() as session:
            result = session.run(query, **params)
            return [dict(rec) for rec in result]

    # ---------------------------------------------------------
    # 4. Get Items by Location
    # ---------------------------------------------------------
    def get_items_by_location(
        self,
        location_name: str,
        limit: int = 50,
        requesting_cpse: Optional[str] = None,
        allow_cross_cpse: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves items stored at a specific CPSE depot/location."""
        if not self.driver:
            return []

        req_cpse, is_cross = self._resolve_auth(requesting_cpse, allow_cross_cpse)
        if not req_cpse and not is_cross:
            raise PermissionError(
                "Access denied: A requesting CPSE or explicit cross-CPSE authorization is required."
            )

        if not is_cross:
            query = """
            MATCH (item:InventoryItem)-[:STORED_AT]->(loc:Location {name: $location_name})
            MATCH (item)-[:OPERATED_BY]->(cpse:CPSE {name: $requesting_cpse})
            OPTIONAL MATCH (item)<-[:HAS_ITEM]-(it:ItemType)
            OPTIONAL MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
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
            params = {"location_name": location_name, "requesting_cpse": req_cpse, "limit": limit}
        else:
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
            params = {"location_name": location_name, "limit": limit}

        with self.driver.session() as session:
            result = session.run(query, **params)
            return [dict(rec) for rec in result]

    # ---------------------------------------------------------
    # 5. Get Surplus by CPSE
    # ---------------------------------------------------------
    def get_cpse_surplus(
        self,
        cpse_name: str,
        min_days_idle: int = 0,
        limit: int = 50,
        requesting_cpse: Optional[str] = None,
        allow_cross_cpse: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns surplus equipment for a given CPSE ordered by days idle.
        Enforces tenant isolation and strips unit_cost_inr on cross-CPSE reads.
        """
        if not self.driver:
            return []

        req_cpse, is_cross = self._resolve_auth(requesting_cpse, allow_cross_cpse)
        target_cpse = cpse_name.strip().upper()

        if req_cpse and req_cpse != target_cpse:
            if not is_cross:
                raise PermissionError(
                    f"Access denied: Requesting CPSE '{req_cpse}' is not authorized to access surplus of '{target_cpse}'. "
                    "Explicit cross-CPSE authorization required."
                )
        elif not req_cpse and not is_cross:
            raise PermissionError(
                "Access denied: A requesting CPSE or explicit cross-CPSE authorization is required."
            )

        query = """
        MATCH (item:InventoryItem)-[:OPERATED_BY]->(cpse:CPSE {name: $cpse_name})
        MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
        WHERE stock.days_idle >= $min_days_idle
        OPTIONAL MATCH (item)<-[:HAS_ITEM]-(it:ItemType)
        OPTIONAL MATCH (item)-[:STORED_AT]->(loc:Location)
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
            result = session.run(query, cpse_name=target_cpse, min_days_idle=min_days_idle, limit=limit)
            rows = []
            for rec in result:
                d = dict(rec)
                if (req_cpse and req_cpse != target_cpse) or (not req_cpse and is_cross):
                    d.pop("unit_cost_inr", None)
                rows.append(d)
            return rows

    # ---------------------------------------------------------
    # 6. Get Idle Items
    # ---------------------------------------------------------
    def get_idle_items(
        self,
        min_days_idle: int = 90,
        limit: int = 50,
        requesting_cpse: Optional[str] = None,
        allow_cross_cpse: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Returns non-moving/dormant items, scoped to authorized requesting CPSE."""
        if not self.driver:
            return []

        req_cpse, is_cross = self._resolve_auth(requesting_cpse, allow_cross_cpse)
        if not req_cpse and not is_cross:
            raise PermissionError(
                "Access denied: A requesting CPSE or explicit cross-CPSE authorization is required."
            )

        if not is_cross:
            query = """
            MATCH (item:InventoryItem)-[:HAS_STOCK_INFO]->(stock:StockInfo)
            MATCH (item)-[:OPERATED_BY]->(cpse:CPSE {name: $requesting_cpse})
            WHERE stock.days_idle >= $min_days_idle
            OPTIONAL MATCH (item)<-[:HAS_ITEM]-(it:ItemType)
            OPTIONAL MATCH (item)-[:STORED_AT]->(loc:Location)
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
            params = {"min_days_idle": min_days_idle, "requesting_cpse": req_cpse, "limit": limit}
        else:
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
            params = {"min_days_idle": min_days_idle, "limit": limit}

        with self.driver.session() as session:
            result = session.run(query, **params)
            rows = []
            for rec in result:
                d = dict(rec)
                if (req_cpse and d.get("cpse") != req_cpse) or (not req_cpse and is_cross):
                    d.pop("unit_cost_inr", None)
                rows.append(d)
            return rows

    # ---------------------------------------------------------
    # 7. Get Material Specification
    # ---------------------------------------------------------
    def get_item_specification(
        self,
        sku_code: str,
        requesting_cpse: Optional[str] = None,
        allow_cross_cpse: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Fetches the consolidated MaterialSpecification node for an item with authorization check."""
        if not self.driver:
            return {}

        req_cpse, is_cross = self._resolve_auth(requesting_cpse, allow_cross_cpse)
        if not req_cpse and not is_cross:
            raise PermissionError(
                "Access denied: A requesting CPSE or explicit cross-CPSE authorization is required. "
                "A SKU alone does not grant access to inventory specifications."
            )

        query = """
        MATCH (item:InventoryItem {sku_code: $sku_code})
        OPTIONAL MATCH (item)-[:OPERATED_BY]->(cpse:CPSE)
        OPTIONAL MATCH (item)-[:HAS_SPECIFICATION]->(spec:MaterialSpecification)
        RETURN cpse.name AS cpse, properties(spec) AS specification
        """

        with self.driver.session() as session:
            record = session.run(query, sku_code=sku_code).single()
            if not record:
                return {}

            item_cpse = record["cpse"]
            if req_cpse and item_cpse and item_cpse != req_cpse and not is_cross:
                raise PermissionError(
                    f"Access denied: Requesting CPSE '{req_cpse}' is not authorized to access specification "
                    f"for SKU '{sku_code}' owned by '{item_cpse}'."
                )

            if record["specification"]:
                return dict(record["specification"])
        return {}

    # ---------------------------------------------------------
    # 8. Hierarchical Path (Item -> ItemType -> InventoryItem -> Branches)
    # ---------------------------------------------------------
    def get_item_hierarchy(
        self,
        sku_code: str,
        requesting_cpse: Optional[str] = None,
        allow_cross_cpse: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Demonstrates top-down hierarchical traversal for visualization with tenant isolation."""
        if not self.driver:
            return {}

        req_cpse, is_cross = self._resolve_auth(requesting_cpse, allow_cross_cpse)
        if not req_cpse and not is_cross:
            raise PermissionError(
                "Access denied: A requesting CPSE or explicit cross-CPSE authorization is required. "
                "A SKU alone does not grant access to inventory hierarchy."
            )

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
            tender.tender_ref AS tender_ref,
            cpse.name AS cpse,
            properties(spec) AS specification
        """

        with self.driver.session() as session:
            record = session.run(query, sku_code=sku_code).single()
            if not record:
                return {}

            data = dict(record)
            item_cpse = data.get("cpse")
            if req_cpse and item_cpse and item_cpse != req_cpse:
                if not is_cross:
                    raise PermissionError(
                        f"Access denied: Requesting CPSE '{req_cpse}' is not authorized to access hierarchy "
                        f"of SKU '{sku_code}' owned by '{item_cpse}'."
                    )
                data = self._strip_commercial_fields_item(data)
            elif not req_cpse and is_cross:
                data = self._strip_commercial_fields_item(data)

            return data

    # ---------------------------------------------------------
    # 9. Dynamic Engineering Compatibility Search
    # ---------------------------------------------------------
    def find_compatible_surplus(
        self,
        item_type: str,
        nominal_bore_mm: float,
        pressure_rating_bar: float,
        requesting_cpse: Optional[str] = None,
        allow_cross_cpse: Optional[bool] = None,
        min_days_idle: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Finds candidate surplus equipment matching engineering requirements on the approved unified graph:
        - Exact dimensional parity on nominal_bore_mm (tolerance <= 0.1 mm).
        - Safe pressure threshold parity on pressure_rating_bar (candidate >= required).
        - Positive stock quantity and idle dormancy filter.
        - Strict cross-CPSE commercial price isolation.

        Safety Invariant:
        Requires valid positive engineering properties. Never guesses missing properties
        or claims safety based solely on description similarity. Missing properties
        result in an explicit ValueError.
        """
        if not self.driver:
            return []

        # 1. Engineering Property Validation - Zero hallucination / Zero guess invariant
        if not item_type or not str(item_type).strip():
            raise ValueError("Parameter 'item_type' is required for engineering compatibility search.")

        try:
            nb = float(nominal_bore_mm)
            if nb <= 0.0:
                raise ValueError()
        except (TypeError, ValueError):
            raise ValueError(
                f"Invalid or missing 'nominal_bore_mm' ({nominal_bore_mm}): "
                "Must be a positive float. Engineering dimensions cannot be inferred or guessed."
            )

        try:
            pr = float(pressure_rating_bar)
            if pr <= 0.0:
                raise ValueError()
        except (TypeError, ValueError):
            raise ValueError(
                f"Invalid or missing 'pressure_rating_bar' ({pressure_rating_bar}): "
                "Must be a positive float. Pressure ratings cannot be inferred or guessed."
            )

        # 2. Authorization scoping: default allow_cross_cpse is True for mutual aid mesh,
        # but commercial prices are strictly stripped across enterprises.
        req_cpse = requesting_cpse.strip().upper() if requesting_cpse else self.requesting_cpse
        is_cross = True if allow_cross_cpse is None else bool(allow_cross_cpse)

        if not req_cpse and not is_cross:
            raise PermissionError(
                "Access denied: A requesting CPSE or explicit cross-CPSE authorization is required to search surplus."
            )

        # 3. Cypher Traversal on Approved Unified Graph
        query = """
        MATCH (root:Item)-[:HAS_ITEM_TYPE]->(it:ItemType {name: $item_type})-[:HAS_ITEM]->(item:InventoryItem)
        MATCH (item)-[:HAS_STOCK_INFO]->(stock:StockInfo)
        MATCH (item)-[:STORED_AT]->(loc:Location)-[:IN_STATE]->(state:State)
        MATCH (item)-[:OPERATED_BY]->(cpse:CPSE)

        WHERE abs(item.nominal_bore_mm - $nominal_bore_mm) < 0.1
          AND item.pressure_rating_bar >= $pressure_rating_bar
          AND stock.quantity > 0
          AND stock.days_idle >= $min_days_idle
          AND ($scope_cpse IS NULL OR cpse.name = $scope_cpse)

        OPTIONAL MATCH (item)-[:HAS_SPECIFICATION]->(spec:MaterialSpecification)

        RETURN
            item.sku_code AS sku_code,
            it.name AS item_type,
            item.nominal_bore_mm AS nominal_bore_mm,
            item.pressure_rating_bar AS pressure_rating_bar,
            item.make_in_india_class AS make_in_india_class,
            item.local_content_percentage AS local_content_percentage,
            stock.quantity AS quantity,
            stock.days_idle AS days_idle,
            stock.unit_cost_inr AS unit_cost_inr,
            loc.name AS location,
            state.name AS state,
            cpse.name AS cpse,
            properties(spec) AS specification
        ORDER BY stock.days_idle DESC, item.pressure_rating_bar ASC
        LIMIT $limit
        """

        scope_cpse = None if is_cross else req_cpse
        params = {
            "item_type": item_type.strip(),
            "nominal_bore_mm": nb,
            "pressure_rating_bar": pr,
            "min_days_idle": min_days_idle,
            "scope_cpse": scope_cpse,
            "limit": limit,
        }

        with self.driver.session() as session:
            result = session.run(query, **params)
            candidates = []
            for rec in result:
                d = dict(rec)
                cand_pr = float(d.get("pressure_rating_bar") or 0.0)
                if abs(cand_pr - pr) < 0.01:
                    d["compatibility_status"] = "EXACT_SPECIFICATION_MATCH"
                else:
                    d["compatibility_status"] = "SAFE_PRESSURE_UPGRADE"

                # Commercial privacy enforcement
                if (req_cpse and d.get("cpse") != req_cpse) or (not req_cpse and is_cross):
                    d.pop("unit_cost_inr", None)

                candidates.append(d)
            return candidates

    # ---------------------------------------------------------
    # 10. All Item Types with Counts
    # ---------------------------------------------------------
    def get_all_item_types(self, requesting_cpse: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all ItemType categories with inventory counts, optionally scoped to CPSE."""
        if not self.driver:
            return []

        req_cpse = requesting_cpse.strip().upper() if requesting_cpse else self.requesting_cpse

        if req_cpse:
            query = """
            MATCH (root:Item)-[:HAS_ITEM_TYPE]->(it:ItemType)
            OPTIONAL MATCH (it)-[:HAS_ITEM]->(item:InventoryItem)-[:OPERATED_BY]->(cpse:CPSE {name: $cpse_name})
            RETURN
                it.name AS item_type,
                count(item) AS count
            ORDER BY count DESC
            """
            params = {"cpse_name": req_cpse}
        else:
            query = """
            MATCH (root:Item)-[:HAS_ITEM_TYPE]->(it:ItemType)
            OPTIONAL MATCH (it)-[:HAS_ITEM]->(item:InventoryItem)
            RETURN
                it.name AS item_type,
                count(item) AS count
            ORDER BY count DESC
            """
            params = {}

        with self.driver.session() as session:
            result = session.run(query, **params)
            return [dict(rec) for rec in result]

    # ---------------------------------------------------------
    # 11. Graph Topology Summary
    # ---------------------------------------------------------
    def get_graph_topology(self) -> Dict[str, Any]:
        """Provides node and relationship counts verifying the unified graph structure."""
        if not self.driver:
            return {}

        query = """
        CALL apoc.meta.stats() YIELD nodeCount, relCount, labels, relTypes
        RETURN nodeCount, relCount, labels, relTypes
        """

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
