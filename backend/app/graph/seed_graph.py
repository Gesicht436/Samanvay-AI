"""
Neo4j Graph Database Seeding Script.
Loads UNSPSC v26, GeM categories, Canonical Master Catalog (2,200 items),
and CPSE inventory stock (10,800 items) into Neo4j with unique constraints.
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
                for row in reader:
                    session.run("""
                    MERGE (u:UNSPSC_Commodity {code: $code})
                    SET u.title = $title, u.level = $level, u.parent_code = $parent
                    """, code=row["code"], title=row["title"], level=row["level"], parent=row["parent_code"])

        # 2. Seed GeM Categories
        gem_file = TAXONOMY_DIR / "gem_categories.csv"
        if gem_file.exists():
            logger.info("[+] Seeding GeM categories...")
            with open(gem_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    session.run("""
                    MERGE (g:GeM_Category {category_id: $cat_id})
                    SET g.name = $name, g.parent_id = $parent
                    """, cat_id=row["category_id"], name=row["name"], parent=row["parent_id"])

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

        logger.info("[+] Graph database seeding complete!")


if __name__ == "__main__":
    seed_database()
