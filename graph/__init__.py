"""
Samanvay-AI Knowledge Graph Module.

Conforms to the Dataset 1 Unified Architecture:
(:Item) -> [:HAS_ITEM_TYPE] -> (:ItemType) -> [:HAS_ITEM] -> (:InventoryItem)
    ├── [:HAS_STOCK_INFO]   -> (:StockInfo)
    ├── [:STORED_AT]        -> (:Location) -> [:IN_STATE] -> (:State)
    ├── [:ORDERED_BY]       -> (:PurchaseOrder) -> [:PART_OF_TENDER] -> (:CPPPTender)
    ├── [:OPERATED_BY]      -> (:CPSE)
    └── [:HAS_SPECIFICATION]-> (:MaterialSpecification)
"""

from .schema import NodeTypes, RelTypes, CompatEdges
from .logistics import (
    haversine_distance,
    road_distance,
    estimate_transit_hours,
    estimate_freight_cost_inr,
    compute_co2_saved,
    get_nearest_depots,
    compute_route_summary,
    DEPOT_COORDINATES,
)
from .queries import GraphQuerier
from .syncer import Neo4jSyncer, GraphSyncer
from .seed_graph import GraphSeeder, extract_item_type

__all__ = [
    "NodeTypes",
    "RelTypes",
    "CompatEdges",
    "haversine_distance",
    "road_distance",
    "estimate_transit_hours",
    "estimate_freight_cost_inr",
    "compute_co2_saved",
    "get_nearest_depots",
    "compute_route_summary",
    "DEPOT_COORDINATES",
    "GraphQuerier",
    "Neo4jSyncer",
    "GraphSyncer",
    "GraphSeeder",
    "extract_item_type",
]
