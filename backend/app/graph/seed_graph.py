"""
Neo4j Graph Database Seeding Script.
Loads UNSPSC v26, GeM categories, Canonical Master Catalog (2,200 items),
and CPSE inventory stock (10,800 items across IOCL, ONGC, and BPCL) into Neo4j with unique constraints.
"""

import csv
import logging
from pathlib import Path
from backend.app.graph.client import get_neo4j_driver
from backend.app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = settings.DATA_DIR
TAXONOMY_DIR = settings.TAXONOMIES_DIR
CATALOG_DIR = settings.MOCK_CATALOGS_DIR


def seed_database():
    driver = get_neo4j_driver()
    if driver is None:
        logger.error("[-] Neo4j driver unavailable. Ensure Neo4j container is running.")
        return

    with driver.session() as session:
        logger.info("[+] Setting up Neo4j unique constraints...")
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:CanonicalMaterial) REQUIRE c.canonical_id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (u:UNSPSC_Commodity) REQUIRE u.code IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (g:GeM_Category) REQUIRE g.category_id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:CPSE_Depot) REQUIRE d.depot_id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:LegacySKU) REQUIRE s.local_code IS UNIQUE;"
        ]
        for c in constraints:
            session.run(c)

        # 1. Seed UNSPSC
        unspsc_file = TAXONOMY_DIR / "unspsc_v26.csv"
        if unspsc_file.exists():
            logger.info("[+] Seeding UNSPSC taxonomy...")
            with open(unspsc_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                batch = []
                for row in reader:
                    batch.append(row)
                    if len(batch) >= 500:
                        session.run("""
                        UNWIND $batch AS item
                        MERGE (u:UNSPSC_Commodity {code: item.code})
                        SET u.title = item.title, u.level = item.level, u.parent_code = item.parent_code
                        """, batch=batch)
                        batch = []
                if batch:
                    session.run("""
                    UNWIND $batch AS item
                    MERGE (u:UNSPSC_Commodity {code: item.code})
                    SET u.title = item.title, u.level = item.level, u.parent_code = item.parent_code
                    """, batch=batch)

        # 2. Seed GeM Categories
        gem_file = TAXONOMY_DIR / "gem_categories.csv"
        if gem_file.exists():
            logger.info("[+] Seeding GeM categories...")
            with open(gem_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                batch = []
                for row in reader:
                    batch.append(row)
                    if len(batch) >= 500:
                        session.run("""
                        UNWIND $batch AS item
                        MERGE (g:GeM_Category {category_id: item.category_id})
                        SET g.name = item.name, g.parent_id = item.parent_id
                        """, batch=batch)
                        batch = []
                if batch:
                    session.run("""
                    UNWIND $batch AS item
                    MERGE (g:GeM_Category {category_id: item.category_id})
                    SET g.name = item.name, g.parent_id = item.parent_id
                    """, batch=batch)

        # 3. Seed Canonical Master
        canonical_file = TAXONOMY_DIR / "canonical_master.csv"
        if canonical_file.exists():
            logger.info("[+] Seeding 2,200 Canonical Materials...")
            with open(canonical_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                batch = []
                for row in reader:
                    batch.append(row)
                    if len(batch) >= 200:
                        session.run("""
                        UNWIND $batch AS item
                        MERGE (c:CanonicalMaterial {canonical_id: item.canonical_id})
                        SET c.item_type = item.item_type,
                            c.size_nb_mm = toFloat(item.size_nb_mm),
                            c.pressure_class = toInteger(item.pressure_class),
                            c.metallurgy = item.metallurgy,
                            c.facing_end = item.facing_end,
                            c.standard = item.standard,
                            c.canonical_description = item.canonical_description
                        WITH c, item
                        MATCH (u:UNSPSC_Commodity {code: item.unspsc_code})
                        MERGE (c)-[:CLASSIFIED_UNDER]->(u)
                        WITH c, item
                        MATCH (g:GeM_Category {category_id: item.gem_category_id})
                        MERGE (c)-[:LISTED_ON_GEM]->(g)
                        """, batch=batch)
                        batch = []
                if batch:
                    session.run("""
                    UNWIND $batch AS item
                    MERGE (c:CanonicalMaterial {canonical_id: item.canonical_id})
                    SET c.item_type = item.item_type,
                        c.size_nb_mm = toFloat(item.size_nb_mm),
                        c.pressure_class = toInteger(item.pressure_class),
                        c.metallurgy = item.metallurgy,
                        c.facing_end = item.facing_end,
                        c.standard = item.standard,
                        c.canonical_description = item.canonical_description
                    WITH c, item
                    MATCH (u:UNSPSC_Commodity {code: item.unspsc_code})
                    MERGE (c)-[:CLASSIFIED_UNDER]->(u)
                    WITH c, item
                    MATCH (g:GeM_Category {category_id: item.gem_category_id})
                    MERGE (c)-[:LISTED_ON_GEM]->(g)
                    """, batch=batch)

        # 4. Seed CPSE Catalogs & Depots (IOCL, ONGC, BPCL)
        catalog_files = [
            CATALOG_DIR / "iocl_materials.csv",
            CATALOG_DIR / "ongc_materials.csv",
            CATALOG_DIR / "bpcl_materials.csv",
        ]
        for cat_file in catalog_files:
            if not cat_file.exists():
                continue
            logger.info(f"[+] Seeding enterprise inventory from {cat_file.name}...")
            with open(cat_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                batch = []
                for row in reader:
                    batch.append(row)
                    if len(batch) >= 200:
                        session.run("""
                        UNWIND $batch AS item
                        MERGE (d:CPSE_Depot {depot_id: item.depot_id})
                        SET d.location_name = item.depot_location, d.cpse = item.cpse

                        MERGE (s:LegacySKU {local_code: item.local_code})
                        SET s.cpse = item.cpse,
                            s.raw_description = item.raw_description

                        WITH s, d, item
                        MATCH (c:CanonicalMaterial {canonical_id: item.canonical_id})
                        MERGE (s)-[:MAPS_TO]->(c)

                        WITH s, d, item
                        MERGE (s)-[stock:STORED_AT]->(d)
                        SET stock.quantity = toInteger(item.quantity),
                            stock.unit_cost = toFloat(item.unit_cost_inr),
                            stock.idle_days = toInteger(item.idle_days)
                        """, batch=batch)
                        batch = []
                if batch:
                    session.run("""
                    UNWIND $batch AS item
                    MERGE (d:CPSE_Depot {depot_id: item.depot_id})
                    SET d.location_name = item.depot_location, d.cpse = item.cpse

                    MERGE (s:LegacySKU {local_code: item.local_code})
                    SET s.cpse = item.cpse,
                        s.raw_description = item.raw_description

                    WITH s, d, item
                    MATCH (c:CanonicalMaterial {canonical_id: item.canonical_id})
                    MERGE (s)-[:MAPS_TO]->(c)

                    WITH s, d, item
                    MERGE (s)-[stock:STORED_AT]->(d)
                    SET stock.quantity = toInteger(item.quantity),
                        stock.unit_cost = toFloat(item.unit_cost_inr),
                        stock.idle_days = toInteger(item.idle_days)
                    """, batch=batch)

        logger.info("[+] Complete enterprise graph database seeding finished!")


if __name__ == "__main__":
    seed_database()
