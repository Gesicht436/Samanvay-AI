import pytest
from neo4j import GraphDatabase
from graph.queries import GraphQuerier
from graph.syncer import Neo4jSyncer, GraphSyncer
from graph.schema import NodeTypes, RelTypes
import os
from dotenv import load_dotenv

load_dotenv("e:/Samanvay-AI/.env")
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
pwd = os.getenv("NEO4J_PASSWORD", "samanvay_graph")


def _is_neo4j_live() -> bool:
    try:
        d = GraphDatabase.driver(uri, auth=(user, pwd))
        d.verify_connectivity()
        d.close()
        return True
    except Exception:
        return False


NEO4J_LIVE = _is_neo4j_live()


@pytest.mark.skipif(not NEO4J_LIVE, reason="Live Neo4j instance not reachable at configured URI")
def test_unified_graph_structure():
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    with driver.session() as s:
        # 1. Root node Item
        item_root = s.run("MATCH (n:Item) RETURN n.name as name").single()
        assert item_root is not None, "Root (:Item) node is missing!"
        assert item_root["name"] == "Item"

        # 2. HAS_ITEM_TYPE downwards from Item to ItemType
        item_types = s.run("MATCH (root:Item)-[:HAS_ITEM_TYPE]->(it:ItemType) RETURN count(it) as count").single()["count"]
        assert item_types > 0, "No ItemTypes connected to root Item!"

        # 3. HAS_ITEM downwards from ItemType to InventoryItem
        items_under_types = s.run("MATCH (it:ItemType)-[:HAS_ITEM]->(i:InventoryItem) RETURN count(i) as count").single()["count"]
        assert items_under_types > 0, "No InventoryItems connected to ItemTypes!"

        # 4. Outgoing relationships from InventoryItem
        stock_rels = s.run("MATCH (i:InventoryItem)-[:HAS_STOCK_INFO]->(s:StockInfo) RETURN count(s) as count").single()["count"]
        assert stock_rels == items_under_types, "Every InventoryItem must have HAS_STOCK_INFO to StockInfo"

        loc_rels = s.run("MATCH (i:InventoryItem)-[:STORED_AT]->(l:Location) RETURN count(l) as count").single()["count"]
        assert loc_rels == items_under_types, "Every InventoryItem must be STORED_AT Location"

        state_rels = s.run("MATCH (l:Location)-[:IN_STATE]->(st:State) RETURN count(st) as count").single()["count"]
        assert state_rels > 0, "Location must connect IN_STATE to State"

        po_rels = s.run("MATCH (i:InventoryItem)-[:ORDERED_BY]->(po:PurchaseOrder) RETURN count(po) as count").single()["count"]
        assert po_rels == items_under_types, "Every InventoryItem must be ORDERED_BY PurchaseOrder"

        cpse_rels = s.run("MATCH (i:InventoryItem)-[:OPERATED_BY]->(c:CPSE) RETURN count(c) as count").single()["count"]
        assert cpse_rels == items_under_types, "Every InventoryItem must be OPERATED_BY CPSE"

        spec_rels = s.run("MATCH (i:InventoryItem)-[:HAS_SPECIFICATION]->(m:MaterialSpecification) RETURN count(m) as count").single()["count"]
        assert spec_rels == items_under_types, "Every InventoryItem must have HAS_SPECIFICATION to MaterialSpecification"

        # 5. Check forbidden nodes (must have 0 instances)
        forbidden_labels = [
            "Depot", "CanonicalMaterial", "Heat", "Size", "PressureClass",
            "MaterialGrade", "RawDescription", "Standard", "HSNCode",
            "MESCCode", "GeMCategory", "IndianStandard", "OilSpecification",
            "OilMaterialCode"
        ]
        for fl in forbidden_labels:
            cnt = s.run(f"MATCH (n:`{fl}`) RETURN count(n) as count").single()["count"]
            assert cnt == 0, f"Forbidden label '{fl}' has {cnt} nodes in the graph!"

        # 6. Check MaterialSpecification properties
        spec_sample = s.run("MATCH (m:MaterialSpecification) RETURN properties(m) as p LIMIT 1").single()["p"]
        expected_spec_props = [
            "raw_description", "standard", "hsn_code", "mesc_code",
            "gem_category", "gem_category_id", "indian_standard",
            "oil_std_spec", "oil_material_code"
        ]
        for prop in expected_spec_props:
            assert prop in spec_sample, f"Property '{prop}' missing on MaterialSpecification!"

        # 7. Check InventoryItem properties
        item_sample = s.run("MATCH (i:InventoryItem) RETURN properties(i) as p LIMIT 1").single()["p"]
        expected_item_props = [
            "sku_code", "heat_no", "nominal_bore_mm", "pressure_rating_bar",
            "make_in_india_class", "local_content_percentage"
        ]
        for prop in expected_item_props:
            assert prop in item_sample, f"Property '{prop}' missing on InventoryItem!"

    driver.close()

@pytest.mark.skipif(not NEO4J_LIVE, reason="Live Neo4j instance not reachable at configured URI")
def test_graph_querier():
    querier = GraphQuerier(uri, user, pwd, requesting_cpse="OIL")
    try:
        # Test get_item_by_sku
        item_data = querier.get_item_by_sku("OIL-STU-00001")
        assert item_data != {}
        assert item_data["root_item"] == "Item"
        assert item_data["item_type"] == "Stud Bolt"
        assert item_data["item"]["sku_code"] == "OIL-STU-00001"
        assert "quantity" in item_data["stock"]
        assert item_data["location"] is not None
        assert item_data["state"] == "Assam"
        assert item_data["po_no"] is not None
        assert item_data["cpse"] == "OIL"
        assert item_data["specification"]["raw_description"] is not None

        # Test hierarchy
        hier = querier.get_item_hierarchy("OIL-STU-00001")
        assert hier["root"] == "Item"
        assert hier["item_type"] == "Stud Bolt"
        assert hier["sku_code"] == "OIL-STU-00001"

        # Test get_items_by_item_type (with cross-CPSE authorized flag)
        items = querier.get_items_by_item_type("Stud Bolt", allow_cross_cpse=True)
        assert len(items) > 0
        sku_list = [x["sku_code"] for x in items]
        assert "BPCL-STU-03517" in sku_list or "OIL-STU-00001" in sku_list

        # Test get_items_by_state
        state_items = querier.get_items_by_state("Assam")
        assert len(state_items) > 0

        # Test cpse surplus
        cpse_surplus = querier.get_cpse_surplus("OIL")
        assert len(cpse_surplus) > 0

        # Test item specification
        spec = querier.get_item_specification("OIL-STU-00001")
        assert "raw_description" in spec
        assert "oil_material_code" in spec

        # Test all item types
        types = querier.get_all_item_types()
        assert len(types) > 0
        type_names = [t["item_type"] for t in types]
        assert "Stud Bolt" in type_names

    finally:
        querier.close()


@pytest.mark.skipif(not NEO4J_LIVE, reason="Live Neo4j instance not reachable at configured URI")
def test_graph_syncer():
    syncer = GraphSyncer(uri, user, pwd)
    try:
        # Update days_idle and quantity
        updated = syncer.update_item("OIL-STU-00001", days_idle=99, quantity=65)
        assert updated["stock"]["days_idle"] == 99
        assert updated["stock"]["quantity"] == 65

        # Query back via GraphQuerier to verify update was persisted in DB
        querier = GraphQuerier(uri, user, pwd, requesting_cpse="OIL")
        item = querier.get_item_by_sku("OIL-STU-00001")
        assert item["stock"]["days_idle"] == 99
        assert item["stock"]["quantity"] == 65
        querier.close()

    finally:
        syncer.close()
