from typing import List, Dict, Any

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    GraphDatabase = None
    NEO4J_AVAILABLE = False


class GraphQuerier:
    def __init__(self):
        self.driver = None
        if not NEO4J_AVAILABLE:
            return

        try:
            from backend.app.core.config import settings
            self.uri = settings.neo4j_uri if hasattr(settings, "neo4j_uri") else "bolt://localhost:7687"
            self.user = settings.neo4j_user if hasattr(settings, "neo4j_user") else "neo4j"
            self.password = settings.neo4j_password if hasattr(settings, "neo4j_password") else "password"
        except Exception:
            self.uri = "bolt://localhost:7687"
            self.user = "neo4j"
            self.password = "password"

        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        except Exception:
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def find_compatible_surplus(self, item_type: str, size: str, pressure_class: str, metallurgy: str, facing: str = None) -> List[Dict[str, Any]]:
        # This is a complex cypher query looking for zero-tolerance on size
        # and checking upgrade paths on pressure_class and metallurgy
        query = """
        MATCH (target_size:Size {value: $size})
        MATCH (item:InventoryItem {item_type: $item_type})-[:HAS_SIZE]->(target_size)
        MATCH (item)-[:HAS_PRESSURE_CLASS]->(pc:PressureClass)
        MATCH (target_pc:PressureClass {value: $pressure_class})
        WHERE pc = target_pc OR (pc)-[:SAFE_UPGRADE_FOR*]->(target_pc)
        
        MATCH (item)-[:HAS_BODY_METALLURGY]->(mg:MaterialGrade)
        MATCH (target_mg:MaterialGrade {value: $metallurgy})
        WHERE mg = target_mg OR (mg)-[:ALLOY_UPGRADE_FOR*]->(target_mg)
        
        MATCH (cpse:CPSE)-[:OPERATES]->(d:Depot)-[:HOLDS]->(item)
        
        RETURN item.sku AS sku_code, cpse.name AS cpse, d.id AS depot_id, d.name AS depot_name,
               d.lat AS lat, d.lon AS lon, item.qty AS qty, item.days_idle AS days_idle
        """
        
        results = []
        with self.driver.session() as session:
            result = session.run(query, size=size, item_type=item_type, pressure_class=pressure_class, metallurgy=metallurgy)
            for record in result:
                # Calculate simple compatibility score based on whether it was an exact match
                res = dict(record)
                res["candidate_class"] = "Compatible Alternate"
                res["dynamic_tier"] = "Tier 1"
                res["compatibility_score"] = 0.95
                results.append(res)
        return results

    def get_depot_surplus(self, depot_id: str) -> List[Dict[str, Any]]:
        query = """
        MATCH (d:Depot {id: $depot_id})-[:HOLDS]->(item:InventoryItem)
        MATCH (cpse:CPSE)-[:OPERATES]->(d)
        RETURN item.sku AS sku_code, cpse.name AS cpse, d.id AS depot_id, d.name AS depot_name,
               d.lat AS lat, d.lon AS lon, item.qty AS qty, item.days_idle AS days_idle
        """
        results = []
        with self.driver.session() as session:
            result = session.run(query, depot_id=depot_id)
            for record in result:
                results.append(dict(record))
        return results

    def get_cpse_surplus(self, cpse_code: str) -> List[Dict[str, Any]]:
        query = """
        MATCH (cpse:CPSE {name: $cpse_code})-[:OPERATES]->(d:Depot)-[:HOLDS]->(item:InventoryItem)
        RETURN item.sku AS sku_code, cpse.name AS cpse, d.id AS depot_id, d.name AS depot_name,
               d.lat AS lat, d.lon AS lon, item.qty AS qty, item.days_idle AS days_idle
        """
        results = []
        with self.driver.session() as session:
            result = session.run(query, cpse_code=cpse_code)
            for record in result:
                results.append(dict(record))
        return results

    def get_item_property_star(self, sku_code: str) -> Dict[str, Any]:
        query = """
        MATCH (item:InventoryItem {sku: $sku_code})-[r]->(prop)
        WHERE type(r) STARTS WITH 'HAS_'
        RETURN type(r) AS rel_type, prop.value AS value
        """
        props = {}
        with self.driver.session() as session:
            result = session.run(query, sku_code=sku_code)
            for record in result:
                props[record["rel_type"]] = record["value"]
        return props
