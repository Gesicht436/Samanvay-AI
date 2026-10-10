"""
Samanvay-AI Neo4j Knowledge Graph Seeder (Dataset 1).

Implements the unified architecture:
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

from __future__ import annotations

import argparse
import csv
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase

from graph.schema import NodeTypes, RelTypes, VALID_CPSES

logger = logging.getLogger("samanvay.graph.seeder")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_PATH = PROJECT_ROOT / "datasets" / "inventory_catalog.csv"


# ============================================================
# 1. SETTINGS HELPER
# ============================================================

def get_neo4j_config() -> tuple[str, str, str]:
    """Retrieve Neo4j connection parameters with graceful fallbacks."""
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


# ============================================================
# 2. ITEM TYPE EXTRACTION
# ============================================================

def extract_item_type(raw_description: str) -> str:
    """
    Extracts high-level ItemType category from raw_description.

    Classification rules
    --------------------
    - Text is uppercased and collapsed before matching.
    - Specific item types are checked before generic fallbacks.
    - Word-boundary (\\b) anchors are applied to short or ambiguous tokens to
      prevent false positives (e.g. "CAP" in "CAPACITY", "NUT" in "NUTS",
      "RING" in "SPRING", "TUBE" in "TUBER").
    - The function returns the most specific matching category or
      "General Material" when no rule fires.
    """
    if not raw_description:
        return "General Material"

    text = " ".join(str(raw_description).upper().split())

    # ------------------------------------------------------------------
    # 1. Valves — specific types before generic VLV fallback
    # ------------------------------------------------------------------
    if any(k in text for k in ["BFV", "BUTTERFLY", "VLV-BFV", "VLV BFV"]):
        return "Butterfly Valve"
    if any(k in text for k in ["PSV", "SAFETY RELIEF", "RELIEF VALVE", "VLV-PSV", "VLV PSV"]):
        return "Safety Relief Valve"
    if any(k in text for k in ["VLV BL", "VLV-BL", "BALL VALVE", "BALL-VALVE"]):
        return "Ball Valve"
    if any(k in text for k in ["VLV GT", "VLV-GT", "GATE VALVE", "GATE-VALVE"]):
        return "Gate Valve"
    if any(k in text for k in ["VLV GL", "VLV-GL", "GLOBE VALVE", "GLOBE-VALVE"]):
        return "Globe Valve"
    if any(k in text for k in ["VLV CHK", "VLV-CHK", "CHECK VALVE", "CHECK-VALVE"]):
        return "Check Valve"
    if any(k in text for k in ["PLUG VALVE", "VLV PLG", "VLV-PLG"]):
        return "Plug Valve"
    if any(k in text for k in ["CONTROL VALVE", "VLV CTL", "VLV-CTL"]):
        return "Control Valve"
    if any(k in text for k in ["NEEDLE VALVE", "VLV NDL", "VLV-NDL"]):
        return "Needle Valve"

    # ------------------------------------------------------------------
    # 2. Pipe Fittings
    # ------------------------------------------------------------------
    # ELB / ELBOW — but avoid matching "ELBOW" inside longer words.
    if re.search(r"\bELB\b", text) or re.search(r"\bELBOW\b", text) or "ELB-90" in text:
        return "Elbow"
    # TEE — word-boundary to avoid matching e.g. "STEEL"
    if re.search(r"\bTEE\b", text) or "EQUAL TEE" in text or "REDUCING TEE" in text or "TEE-EQ" in text:
        return "Tee"
    if any(k in text for k in ["RED CONC", "RED-CONC", "CONCENTRIC REDUCER", "ECCENTRIC REDUCER", "RED ECC", "RED-ECC"]):
        return "Reducer"
    # NIPPLE — standalone; avoid matching inside longer tokens if they arise
    if re.search(r"\bNIPPLE\b", text) or re.search(r"\bNIP\b", text):
        return "Nipple"
    if "COUPLING" in text or "CPLG" in text:
        return "Coupling"
    if re.search(r"\bUNION\b", text):
        return "Union"
    # CAP — word-boundary only; avoids matching CAPACITY, CAPS, etc.
    if re.search(r"\bCAP\b", text) and "FITTING" in text:
        return "Cap"
    if "BUTTWELD FITTING" in text or "BW FITTING" in text:
        return "Butt Weld Fitting"

    # ------------------------------------------------------------------
    # 3. Gaskets & Seals
    # ------------------------------------------------------------------
    if any(k in text for k in ["GSKT SWG", "GSKT-SWG", "SPIRAL WOUND GASKET"]):
        return "Spiral Wound Gasket"
    if any(k in text for k in ["GSKT RTJ", "GSKT-RTJ", "RING TYPE JOINT", "RTJ GASKET"]):
        return "Ring Type Joint Gasket"
    if re.search(r"\bGSKT\b", text) or re.search(r"\bGASKET\b", text):
        return "Gasket"
    if any(k in text for k in ["MECH SEAL", "MECHANICAL SEAL", "MECH-SEAL"]):
        return "Mechanical Seal"
    if "O-RING" in text or "ORING" in text:
        return "O-Ring"

    # ------------------------------------------------------------------
    # 4. Flanges — specific before generic FLG fallback
    # ------------------------------------------------------------------
    if any(k in text for k in ["FLG WN", "FLG-WN", "WELD NECK"]):
        return "Weld Neck Flange"
    if any(k in text for k in ["FLG BL", "FLG-BL", "BLIND FLANGE"]):
        return "Blind Flange"
    if any(k in text for k in ["FLG SO", "FLG-SO", "SLIP ON"]):
        return "Slip-On Flange"
    if re.search(r"\bFLG\b", text) or re.search(r"\bFLANGE\b", text):
        return "Flange"

    # ------------------------------------------------------------------
    # 5. Pipes & Tubes
    # ------------------------------------------------------------------
    if any(k in text for k in ["PIPE SMLS", "PIPE-SMLS", "LINE PIPE, SEAMLESS"]) or ("SEAMLESS" in text and "PIPE" in text):
        return "Seamless Pipe"
    if any(k in text for k in ["PIPE ERW", "PIPE-ERW", "LINE PIPE, ELECTRIC"]) or ("ERW" in text and "PIPE" in text):
        return "ERW Pipe"
    if re.search(r"\bPIPE\b", text) or "LINE PIPE" in text:
        return "Pipe"
    # TUBE — word-boundary to avoid matching TUBER, TUBING (handled separately)
    if "TUBING" in text or re.search(r"\bTUBE\b", text):
        return "Tube"

    # ------------------------------------------------------------------
    # 6. Pumps & Spares — specific before generic pump fallback
    # ------------------------------------------------------------------
    if "PUMP SHAFT SLEEVE" in text or "SHAFT SLEEVE" in text:
        return "Pump Shaft Sleeve"
    if "PUMP IMPELLER" in text or "IMPELLER" in text:
        return "Pump Impeller"
    if "PUMP CASING" in text:
        return "Pump Casing"
    if re.search(r"\bPUMP\b", text) or "CENTRIFUGAL" in text:
        return "Centrifugal Pump"

    # ------------------------------------------------------------------
    # 7. Fasteners
    # ------------------------------------------------------------------
    if any(k in text for k in ["STUD BLT", "STUD-BLT", "STUD BOLT", "STUD"]):
        return "Stud Bolt"
    if re.search(r"\bBOLT\b", text) or "HEX BOLT" in text:
        return "Bolt"
    # NUT — word-boundary to avoid matching NUTS (covered), NUTSHELL, etc.
    if re.search(r"\bNUTS?\b", text):
        return "Nut"

    # ------------------------------------------------------------------
    # 8. Mechanical Parts
    # ------------------------------------------------------------------
    if "SLEEVE" in text:
        return "Shaft Sleeve"
    # RING — word-boundary to avoid matching SPRING, BORING, MOORING, etc.
    if re.search(r"\bRING\b", text):
        return "Ring"
    if "BEARING" in text:
        return "Bearing"

    # ------------------------------------------------------------------
    # 9. Generic fallbacks — only reached if no specific rule fired
    # ------------------------------------------------------------------
    if re.search(r"\bVLV\b", text) or re.search(r"\bVALVE\b", text):
        return "Valve"
    if "FITTING" in text:
        return "Fitting"

    return "General Material"


# ============================================================
# 3. CSV RECORD PARSER & CPSE VALIDATION
# ============================================================

def validate_cpse_name(cpse_raw: Any, row_number: Optional[int] = None) -> str:
    """
    Validates CPSE name against the official sovereign CPSE registry.
    Rejects missing, blank, and unregistered CPSE identifiers.
    Never silently defaults an invalid value to 'OIL'.
    """
    prefix = f"Row {row_number}: " if row_number is not None else ""
    if cpse_raw is None:
        raise ValueError(f"{prefix}Missing 'cpse_name': CPSE identifier is required.")

    val = str(cpse_raw).strip()
    if not val:
        raise ValueError(f"{prefix}Blank 'cpse_name': CPSE identifier cannot be blank.")

    upper = val.upper()
    if upper not in VALID_CPSES:
        raise ValueError(
            f"{prefix}Invalid CPSE '{val}': Unknown enterprise. Must be one of registered CPSEs: {', '.join(sorted(VALID_CPSES))}."
        )

    return upper


def parse_csv_row(row: dict[str, str], row_number: Optional[int] = None) -> dict[str, Any]:
    """Cleans and converts raw CSV string fields into structured dictionary for Cypher."""
    raw_desc = (row.get("raw_description") or "").strip()
    item_type = extract_item_type(raw_desc)

    def to_float(val: Optional[str], default: float = 0.0) -> float:
        if not val or not val.strip():
            return default
        try:
            return float(val.strip())
        except ValueError:
            return default

    def to_int(val: Optional[str], default: int = 0) -> int:
        if not val or not val.strip():
            return default
        try:
            return int(float(val.strip()))
        except ValueError:
            return default

    def clean_str(val: Optional[str]) -> Optional[str]:
        if val is None:
            return None
        v = val.strip()
        return v if v else None

    # Validate CPSE strictly against the official registry - never silently default to OIL
    cpse_name = validate_cpse_name(row.get("cpse_name"), row_number=row_number)

    return {
        # ItemType & Root
        "item_type": item_type,

        # InventoryItem
        "sku_code": (row.get("sku_code") or "").strip(),
        "heat_no": clean_str(row.get("heat_no")),
        "nominal_bore_mm": to_float(row.get("nominal_bore_mm")),
        "pressure_rating_bar": to_float(row.get("pressure_rating_bar")),
        "make_in_india_class": clean_str(row.get("make_in_india_class")),
        "local_content_percentage": to_float(row.get("local_content_percentage")),

        # StockInfo
        "quantity": to_int(row.get("quantity")),
        "unit_cost_inr": to_float(row.get("unit_cost_inr")),
        "days_idle": to_int(row.get("days_idle")),

        # Location / State
        "depot_location": (row.get("depot_location") or "Main Depot").strip(),
        "location_state": (row.get("location_state") or "Assam").strip(),

        # PurchaseOrder & Tender
        "po_no": (row.get("po_no") or "PO-UNKNOWN").strip(),
        "cppp_tender_id": clean_str(row.get("cppp_tender_id")),
        "cppp_tender_ref": clean_str(row.get("cppp_tender_ref")),

        # CPSE
        "cpse_name": cpse_name,

        # MaterialSpecification
        "raw_description": raw_desc,
        "standard": clean_str(row.get("standard")),
        "hsn_code": clean_str(row.get("hsn_code")),
        "mesc_code": clean_str(row.get("mesc_code")),
        "gem_category": clean_str(row.get("gem_category")),
        "gem_category_id": clean_str(row.get("gem_category_id")),
        "indian_standard": clean_str(row.get("indian_standard")),
        "oil_std_spec": clean_str(row.get("oil_std_spec")),
        "oil_material_code": clean_str(row.get("oil_material_code")),
    }


# ============================================================
# 4. CYPHER CONSTRAINTS & SEED QUERY
# ============================================================

CONSTRAINTS = [
    """
    CREATE CONSTRAINT item_root_name_unique IF NOT EXISTS
    FOR (n:Item) REQUIRE n.name IS UNIQUE
    """,
    """
    CREATE CONSTRAINT item_type_name_unique IF NOT EXISTS
    FOR (n:ItemType) REQUIRE n.name IS UNIQUE
    """,
    """
    CREATE CONSTRAINT inventory_item_sku_unique IF NOT EXISTS
    FOR (n:InventoryItem) REQUIRE n.sku_code IS UNIQUE
    """,
    """
    CREATE CONSTRAINT stock_info_sku_unique IF NOT EXISTS
    FOR (n:StockInfo) REQUIRE n.sku_code IS UNIQUE
    """,
    """
    CREATE CONSTRAINT location_name_unique IF NOT EXISTS
    FOR (n:Location) REQUIRE n.name IS UNIQUE
    """,
    """
    CREATE CONSTRAINT state_name_unique IF NOT EXISTS
    FOR (n:State) REQUIRE n.name IS UNIQUE
    """,
    """
    CREATE CONSTRAINT purchase_order_no_unique IF NOT EXISTS
    FOR (n:PurchaseOrder) REQUIRE n.po_no IS UNIQUE
    """,
    """
    CREATE CONSTRAINT cppp_tender_id_unique IF NOT EXISTS
    FOR (n:CPPPTender) REQUIRE n.tender_id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT cpse_name_unique IF NOT EXISTS
    FOR (n:CPSE) REQUIRE n.name IS UNIQUE
    """,
    """
    CREATE CONSTRAINT material_specification_sku_unique IF NOT EXISTS
    FOR (n:MaterialSpecification) REQUIRE n.sku_code IS UNIQUE
    """,
]

SEED_BATCH_QUERY = """
UNWIND $rows AS row

// 1. Single Root Node
MERGE (root:Item {name: "Item"})

// 2. ItemType Node (pointing downward from Item)
MERGE (item_type:ItemType {name: row.item_type})
MERGE (root)-[:HAS_ITEM_TYPE]->(item_type)

// 3. InventoryItem Node (pointing downward from ItemType)
MERGE (item:InventoryItem {sku_code: row.sku_code})
SET item.heat_no = row.heat_no,
    item.nominal_bore_mm = row.nominal_bore_mm,
    item.pressure_rating_bar = row.pressure_rating_bar,
    item.make_in_india_class = row.make_in_india_class,
    item.local_content_percentage = row.local_content_percentage

MERGE (item_type)-[:HAS_ITEM]->(item)

// 4. StockInfo Node
MERGE (stock:StockInfo {sku_code: row.sku_code})
SET stock.quantity = row.quantity,
    stock.unit_cost_inr = row.unit_cost_inr,
    stock.days_idle = row.days_idle

MERGE (item)-[:HAS_STOCK_INFO]->(stock)

// 5. Location & State Nodes
MERGE (location:Location {name: row.depot_location})
MERGE (state:State {name: row.location_state})

MERGE (item)-[:STORED_AT]->(location)
MERGE (location)-[:IN_STATE]->(state)

// 6. PurchaseOrder & CPPPTender Nodes
MERGE (po:PurchaseOrder {po_no: row.po_no})
MERGE (item)-[:ORDERED_BY]->(po)

FOREACH (_ IN CASE
    WHEN row.cppp_tender_id IS NOT NULL AND trim(row.cppp_tender_id) <> ''
    THEN [1]
    ELSE []
END |
    MERGE (tender:CPPPTender {tender_id: row.cppp_tender_id})
    SET tender.tender_ref = row.cppp_tender_ref
    MERGE (po)-[:PART_OF_TENDER]->(tender)
)

// 7. CPSE Node
MERGE (cpse:CPSE {name: row.cpse_name})
MERGE (item)-[:OPERATED_BY]->(cpse)

// 8. Consolidated MaterialSpecification Node
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


# ============================================================
# 5. GRAPH SEEDER CLASS
# ============================================================

class GraphSeeder:
    """Manages database connection, schema setup, CSV parsing, and batch ingestion."""

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        c_uri, c_user, c_pwd = get_neo4j_config()
        self.uri = uri or c_uri
        self.user = user or c_user
        self.password = password or c_pwd
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        if self.driver:
            self.driver.close()

    def create_constraints(self):
        """Initializes unique index constraints across all node types."""
        with self.driver.session() as session:
            for c_query in CONSTRAINTS:
                try:
                    session.run(c_query).consume()
                except Exception as e:
                    logger.warning(f"Constraint notice: {e}")

    def clear_database(self):
        """Removes existing graph elements and cleans deprecated schema constraints."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n").consume()
            
            # Drop any legacy constraints on forbidden/deprecated node types
            deprecated_labels = {
                "Depot", "Size", "PressureClass", "MaterialGrade",
                "RawDescription", "Standard", "HSNCode", "MESCCode",
                "GeMCategory", "IndianStandard", "OilSpecification", "OilMaterialCode"
            }
            try:
                constraints = session.run("SHOW CONSTRAINTS").data()
                for c in constraints:
                    labels = set(c.get("labelsOrTypes", []))
                    if labels & deprecated_labels:
                        c_name = c.get("name")
                        session.run(f"DROP CONSTRAINT `{c_name}` IF EXISTS").consume()
            except Exception as e:
                logger.warning(f"Notice while dropping deprecated constraints: {e}")

    def seed_from_csv(
        self,
        csv_path: Optional[Path] = None,
        max_rows: Optional[int] = None,
        batch_size: int = 250,
        reset: bool = False,
    ) -> int:
        """
        Loads CSV dataset and ingests into Neo4j in high-throughput batches.
        Returns total number of items inserted.
        """
        path = csv_path or DEFAULT_DATASET_PATH
        if not path.exists():
            raise FileNotFoundError(f"Inventory dataset not found at: {path}")

        if reset:
            print("[GraphSeeder] Resetting database for clean Unified Architecture...")
            self.clear_database()

        print("[GraphSeeder] Applying uniqueness constraints...")
        self.create_constraints()

        rows: List[Dict[str, Any]] = []
        rejected_rows: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for idx, r in enumerate(reader, start=1):
                try:
                    rows.append(parse_csv_row(r, row_number=idx))
                except Exception as e:
                    logger.error(f"Row {idx} parse failure: {e}")
                    rejected_rows.append({
                        "row_number": idx,
                        "sku_code": (r.get("sku_code") or "N/A").strip(),
                        "reason": str(e),
                    })

                if max_rows and len(rows) >= max_rows:
                    break

        total = len(rows)
        if rejected_rows:
            logger.warning(
                f"[GraphSeeder] Encounted {len(rejected_rows)} invalid rows during CSV ingestion."
            )
            for rej in rejected_rows[:10]:
                logger.warning(f"  - Row {rej['row_number']} (SKU: {rej['sku_code']}): {rej['reason']}")
            if len(rejected_rows) > 10:
                logger.warning(f"  ... and {len(rejected_rows) - 10} more rejected rows.")
        self.rejected_rows = rejected_rows

        print(f"[GraphSeeder] Prepared {total} rows for ingestion ({len(rejected_rows)} rejected).")

        with self.driver.session() as session:
            for start in range(0, total, batch_size):
                batch = rows[start:start + batch_size]
                session.run(SEED_BATCH_QUERY, rows=batch).consume()
                print(f"  Inserted rows {start + 1}-{min(start + batch_size, total)} of {total}...")

        print(f"[GraphSeeder] Successfully seeded {total} inventory items.")
        return total


# ============================================================
# 6. MAIN CLI ENTRY POINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Samanvay-AI Neo4j Knowledge Graph Seeder")
    parser.add_argument("--dataset", type=str, default=str(DEFAULT_DATASET_PATH), help="Path to inventory_catalog.csv")
    parser.add_argument("--rows", type=int, default=None, help="Limit number of rows (e.g. 1 for testing)")
    parser.add_argument("--batch-size", type=int, default=250, help="Ingestion batch size")
    parser.add_argument("--reset", action="store_true", help="Clear existing graph nodes before seeding")
    args = parser.parse_args()

    seeder = GraphSeeder()
    try:
        seeder.driver.verify_connectivity()
        print(f"Connected to Neo4j at {seeder.uri}")
        seeder.seed_from_csv(
            csv_path=Path(args.dataset),
            max_rows=args.rows,
            batch_size=args.batch_size,
            reset=args.reset,
        )
    finally:
        seeder.close()


if __name__ == "__main__":
    main()
