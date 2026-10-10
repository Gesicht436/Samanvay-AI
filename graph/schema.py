"""
Graph Schema Definitions for Samanvay-AI Neo4j Knowledge Graph.

Architecture conforms to the Dataset 1 Unified Structure:
(:Item)
   ↓ HAS_ITEM_TYPE
(:ItemType)
   ↓ HAS_ITEM
(:InventoryItem)
   ├── HAS_STOCK_INFO ──→ (:StockInfo)
   ├── STORED_AT ───────→ (:Location) ──IN_STATE──→ (:State)
   ├── ORDERED_BY ──────→ (:PurchaseOrder) ──PART_OF_TENDER──→ (:CPPPTender)
   ├── OPERATED_BY ─────→ (:CPSE)
   └── HAS_SPECIFICATION → (:MaterialSpecification)
"""

from enum import Enum


class NodeTypes(str, Enum):
    ITEM = "Item"
    ITEM_TYPE = "ItemType"
    INVENTORY_ITEM = "InventoryItem"
    STOCK_INFO = "StockInfo"
    LOCATION = "Location"
    STATE = "State"
    PURCHASE_ORDER = "PurchaseOrder"
    CPPP_TENDER = "CPPPTender"
    CPSE = "CPSE"
    MATERIAL_SPECIFICATION = "MaterialSpecification"


class RelTypes(str, Enum):
    HAS_ITEM_TYPE = "HAS_ITEM_TYPE"
    HAS_ITEM = "HAS_ITEM"
    HAS_STOCK_INFO = "HAS_STOCK_INFO"
    STORED_AT = "STORED_AT"
    IN_STATE = "IN_STATE"
    ORDERED_BY = "ORDERED_BY"
    PART_OF_TENDER = "PART_OF_TENDER"
    OPERATED_BY = "OPERATED_BY"
    HAS_SPECIFICATION = "HAS_SPECIFICATION"


class CompatEdges(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    SAFE_UPGRADE_FOR = "SAFE_UPGRADE_FOR"
    COMPATIBLE_WITH = "COMPATIBLE_WITH"


# Single Source of Truth for Registered CPSE Organizations
VALID_CPSES: frozenset[str] = frozenset({
    "OIL",
    "NRL",
    "IOCL",
    "ONGC",
    "BPCL",
    "HPCL",
    "GAIL",
})

