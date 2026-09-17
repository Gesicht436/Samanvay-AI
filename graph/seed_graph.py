import logging
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

class GraphSeeder:
    def __init__(self):
        # Graceful fallback if settings not fully available
        try:
            from backend.app.core.config import settings
            self.uri = settings.NEO4J_URI if hasattr(settings, "NEO4J_URI") else "bolt://localhost:7687"
            self.user = settings.NEO4J_USER if hasattr(settings, "NEO4J_USER") else "neo4j"
            self.password = settings.NEO4J_PASSWORD if hasattr(settings, "NEO4J_PASSWORD") else "password"
        except ImportError:
            self.uri = "bolt://localhost:7687"
            self.user = "neo4j"
            self.password = "password"
            
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    def clear_graph(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def seed_cpses(self):
        cpses = ["IOCL", "ONGC", "BPCL", "HPCL", "GAIL"]
        with self.driver.session() as session:
            for cpse in cpses:
                session.run("MERGE (c:CPSE {name: $name})", name=cpse)

    def seed_depots(self):
        depots = [
            {"cpse": "IOCL", "name": "Panipat", "lat": 29.3909, "lon": 76.9635},
            {"cpse": "IOCL", "name": "Mathura", "lat": 27.4924, "lon": 77.6737},
            {"cpse": "IOCL", "name": "Koyali", "lat": 22.3217, "lon": 73.1384},
            {"cpse": "IOCL", "name": "Paradip", "lat": 20.3164, "lon": 86.6085},
            {"cpse": "IOCL", "name": "Barauni", "lat": 25.4714, "lon": 85.9990},
            {"cpse": "IOCL", "name": "Guwahati", "lat": 26.1445, "lon": 91.7362},
            {"cpse": "IOCL", "name": "Digboi", "lat": 27.3834, "lon": 95.6228},
            {"cpse": "ONGC", "name": "Hazira", "lat": 21.1000, "lon": 72.6500},
            {"cpse": "ONGC", "name": "Ankleshwar", "lat": 21.6263, "lon": 73.0025},
            {"cpse": "ONGC", "name": "Uran", "lat": 18.8789, "lon": 72.9341},
            {"cpse": "ONGC", "name": "Mumbai High", "lat": 19.3700, "lon": 71.3800},
            {"cpse": "ONGC", "name": "Rajahmundry", "lat": 17.0005, "lon": 81.8040},
            {"cpse": "BPCL", "name": "Mumbai Mahul", "lat": 19.0252, "lon": 72.8890},
            {"cpse": "BPCL", "name": "Kochi", "lat": 9.9312, "lon": 76.2673},
            {"cpse": "BPCL", "name": "Bina", "lat": 24.1814, "lon": 78.1292},
            {"cpse": "HPCL", "name": "Mumbai", "lat": 19.0176, "lon": 72.8562},
            {"cpse": "HPCL", "name": "Visakh", "lat": 17.6868, "lon": 83.2185},
            {"cpse": "GAIL", "name": "Pata", "lat": 26.4600, "lon": 80.5400},
            {"cpse": "GAIL", "name": "Vijaipur", "lat": 24.1084, "lon": 77.2905}
        ]
        with self.driver.session() as session:
            for depot in depots:
                session.run(
                    """
                    MATCH (c:CPSE {name: $cpse})
                    MERGE (d:Depot {id: $name})
                    SET d.name = $name, d.lat = $lat, d.lon = $lon
                    MERGE (c)-[:OPERATES]->(d)
                    """,
                    cpse=depot["cpse"], name=depot["name"], lat=depot["lat"], lon=depot["lon"]
                )

    def seed_properties_and_upgrades(self):
        with self.driver.session() as session:
            # Pressure Classes and SAFE_UPGRADE_FOR (higher class can substitute lower)
            classes = ["150#", "300#", "600#", "900#", "1500#"]
            for c in classes:
                session.run("MERGE (p:PressureClass {value: $value})", value=c)
            session.run("MATCH (p1:PressureClass {value: '300#'}), (p2:PressureClass {value: '150#'}) MERGE (p1)-[:SAFE_UPGRADE_FOR]->(p2)")
            session.run("MATCH (p1:PressureClass {value: '600#'}), (p2:PressureClass {value: '300#'}) MERGE (p1)-[:SAFE_UPGRADE_FOR]->(p2)")

            # Material Grades and ALLOY_UPGRADE_FOR
            session.run("MERGE (m1:MaterialGrade {value: 'WCB'})")
            session.run("MERGE (m2:MaterialGrade {value: 'CF8M'})")
            session.run("MATCH (m1:MaterialGrade {value: 'CF8M'}), (m2:MaterialGrade {value: 'WCB'}) MERGE (m1)-[:ALLOY_UPGRADE_FOR]->(m2)")

            # Valve Trims and TRIM_UPGRADE_FOR
            session.run("MERGE (t1:ValveTrim {value: 'Trim 1'})")
            session.run("MERGE (t8:ValveTrim {value: 'Trim 8'})")
            session.run("MERGE (t5:ValveTrim {value: 'Trim 5'})")
            session.run("MATCH (t5:ValveTrim {value: 'Trim 5'}), (t8:ValveTrim {value: 'Trim 8'}) MERGE (t5)-[:TRIM_UPGRADE_FOR]->(t8)")
            session.run("MATCH (t8:ValveTrim {value: 'Trim 8'}), (t1:ValveTrim {value: 'Trim 1'}) MERGE (t8)-[:TRIM_UPGRADE_FOR]->(t1)")

            # Port Bore and PORT_UPGRADE_FOR
            session.run("MERGE (pb1:PortBore {value: 'Full Bore'})")
            session.run("MERGE (pb2:PortBore {value: 'Reduced Bore'})")
            session.run("MATCH (pb1:PortBore {value: 'Full Bore'}), (pb2:PortBore {value: 'Reduced Bore'}) MERGE (pb1)-[:PORT_UPGRADE_FOR]->(pb2)")

            # Sizes
            sizes = ["2 inch", "4 inch", "6 inch", "8 inch"]
            for s in sizes:
                session.run("MERGE (sz:Size {value: $value})", value=s)

    def seed_sample_inventory(self):
        with self.driver.session() as session:
            # Example item 1: 4 inch, 150#, WCB, Trim 1, Reduced Bore
            session.run(
                """
                MATCH (d:Depot {name: 'Panipat'})
                MERGE (i:InventoryItem {sku: 'SKU-001'})
                SET i.qty = 10, i.days_idle = 150, i.item_type = 'Gate Valve'
                MERGE (d)-[:HOLDS]->(i)
                WITH i
                MATCH (s:Size {value: '4 inch'})
                MATCH (pc:PressureClass {value: '150#'})
                MATCH (mg:MaterialGrade {value: 'WCB'})
                MATCH (vt:ValveTrim {value: 'Trim 1'})
                MATCH (pb:PortBore {value: 'Reduced Bore'})
                MERGE (i)-[:HAS_SIZE]->(s)
                MERGE (i)-[:HAS_PRESSURE_CLASS]->(pc)
                MERGE (i)-[:HAS_BODY_METALLURGY]->(mg)
                MERGE (i)-[:HAS_TRIM]->(vt)
                MERGE (i)-[:HAS_PORT_BORE]->(pb)
                """
            )
            
            # Example item 2 (Upgrade candidate): 4 inch, 300#, CF8M, Trim 8, Full Bore
            session.run(
                """
                MATCH (d:Depot {name: 'Hazira'})
                MERGE (i:InventoryItem {sku: 'SKU-002'})
                SET i.qty = 5, i.days_idle = 400, i.item_type = 'Gate Valve'
                MERGE (d)-[:HOLDS]->(i)
                WITH i
                MATCH (s:Size {value: '4 inch'})
                MATCH (pc:PressureClass {value: '300#'})
                MATCH (mg:MaterialGrade {value: 'CF8M'})
                MATCH (vt:ValveTrim {value: 'Trim 8'})
                MATCH (pb:PortBore {value: 'Full Bore'})
                MERGE (i)-[:HAS_SIZE]->(s)
                MERGE (i)-[:HAS_PRESSURE_CLASS]->(pc)
                MERGE (i)-[:HAS_BODY_METALLURGY]->(mg)
                MERGE (i)-[:HAS_TRIM]->(vt)
                MERGE (i)-[:HAS_PORT_BORE]->(pb)
                """
            )

    def run_all(self):
        self.clear_graph()
        self.seed_cpses()
        self.seed_depots()
        self.seed_properties_and_upgrades()
        self.seed_sample_inventory()
        self.close()

if __name__ == "__main__":
    seeder = GraphSeeder()
    seeder.run_all()
    print("Graph seeding complete.")
