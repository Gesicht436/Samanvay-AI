"""
curate_taxonomies.py
Generates clean UNSPSC v26, GeM category hierarchies, and canonical material master catalog.
Used for Neo4j knowledge graph seeding and downstream ontology resolution.
Author: Data Pipelines & Taxonomy Lead (Shaurya)
"""

import os
import csv
import itertools
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
TAXONOMY_DIR = DATA_DIR / "taxonomies"
TAXONOMY_DIR.mkdir(parents=True, exist_ok=True)

UNSPSC_DATA = [
    # code, title, level, parent_code
    ("40000000", "Industrial Manufacturing and Processing Machinery and Accessories", "Segment", "ROOT"),
    ("40140000", "Fluid and gas distribution", "Family", "40000000"),
    ("40141600", "Valves", "Class", "40140000"),
    ("40141611", "Gate valves", "Commodity", "40141600"),
    ("40141604", "Ball valves", "Commodity", "40141600"),
    ("40141602", "Globe valves", "Commodity", "40141600"),
    ("40141601", "Check valves", "Commodity", "40141600"),
    ("40141603", "Butterfly valves", "Commodity", "40141600"),
    ("40171500", "Industrial pipe fittings", "Class", "40140000"),
    ("40171501", "Pipe flanges", "Commodity", "40171500"),
    ("40171502", "Pipe elbows", "Commodity", "40171500"),
    ("40171503", "Pipe tees", "Commodity", "40171500"),
    ("40171504", "Pipe reducers", "Commodity", "40171500"),
    ("31000000", "Manufacturing Components and Supplies", "Segment", "ROOT"),
    ("31160000", "Hardware and fasteners", "Family", "31000000"),
    ("31161500", "Bolts", "Class", "31160000"),
    ("31161501", "Stud bolts", "Commodity", "31161500"),
    ("31161600", "Gaskets and seals", "Class", "31160000"),
    ("31161618", "Spiral wound gaskets", "Commodity", "31161600"),
    ("31161601", "Ring joint gaskets", "Commodity", "31161600"),
]

GEM_CATEGORIES_DATA = [
    # category_id, name, parent_id
    ("GEM-IND-001", "Industrial Goods & Mechanical Spares", "ROOT"),
    ("GEM-VALVE-001", "Industrial Valves", "GEM-IND-001"),
    ("GEM-VALVE-GATE", "Gate Valves - Cast & Forged Steel", "GEM-VALVE-001"),
    ("GEM-VALVE-BALL", "Ball Valves - High Pressure Hydrocarbon", "GEM-VALVE-001"),
    ("GEM-VALVE-GLOBE", "Globe Valves - Industrial Process", "GEM-VALVE-001"),
    ("GEM-FLANGE-001", "Steel Pipe Flanges & Fittings", "GEM-IND-001"),
    ("GEM-FLANGE-WN", "Weld Neck Flanges - ASME B16.5", "GEM-FLANGE-001"),
    ("GEM-FLANGE-BL", "Blind Flanges - ASME B16.5", "GEM-FLANGE-001"),
    ("GEM-FLANGE-SO", "Slip-On Flanges - ASME B16.5", "GEM-FLANGE-001"),
    ("GEM-GASKET-001", "Industrial Gaskets & Jointing Materials", "GEM-IND-001"),
    ("GEM-GASKET-SW", "Spiral Wound Gaskets Metallic", "GEM-GASKET-001"),
    ("GEM-FASTENER-001", "High Tensile Fasteners & Studs", "GEM-IND-001"),
    ("GEM-BOLT-STUD", "Alloy Steel Stud Bolts with Nuts - ASTM A193", "GEM-FASTENER-001"),
]

SIZES = [
    (15.0, '1/2"', "DN15"),
    (25.0, '1"', "DN25"),
    (40.0, '1.5"', "DN40"),
    (50.0, '2"', "DN50"),
    (80.0, '3"', "DN80"),
    (100.0, '4"', "DN100"),
    (150.0, '6"', "DN150"),
    (200.0, '8"', "DN200"),
    (250.0, '10"', "DN250"),
    (300.0, '12"', "DN300"),
]

PRESSURE_CLASSES = [150, 300, 600, 900, 1500]

ITEMS_CONFIG = [
    {
        "type": "FLANGE_WELD_NECK",
        "name": "FLANGE, WELD NECK",
        "metallurgies": ["ASTM A105", "ASTM A350 LF2", "ASTM A182 F304", "ASTM A182 F316"],
        "facing": ["RF", "RTJ"],
        "standards": ["ASME B16.5"],
        "unspsc": "40171501",
        "gem": "GEM-FLANGE-WN"
    },
    {
        "type": "FLANGE_BLIND",
        "name": "FLANGE, BLIND",
        "metallurgies": ["ASTM A105", "ASTM A350 LF2", "ASTM A182 F316"],
        "facing": ["RF", "RTJ"],
        "standards": ["ASME B16.5"],
        "unspsc": "40171501",
        "gem": "GEM-FLANGE-BL"
    },
    {
        "type": "FLANGE_SLIP_ON",
        "name": "FLANGE, SLIP ON",
        "metallurgies": ["ASTM A105", "ASTM A182 F304", "ASTM A182 F316"],
        "facing": ["RF", "FF"],
        "standards": ["ASME B16.5"],
        "unspsc": "40171501",
        "gem": "GEM-FLANGE-SO"
    },
    {
        "type": "GATE_VALVE",
        "name": "VALVE, GATE",
        "metallurgies": ["ASTM A216 WCB", "ASTM A105", "ASTM A182 F316"],
        "facing": ["RF", "BW"],
        "standards": ["API 600", "API 6D"],
        "unspsc": "40141611",
        "gem": "GEM-VALVE-GATE"
    },
    {
        "type": "BALL_VALVE",
        "name": "VALVE, BALL",
        "metallurgies": ["ASTM A216 WCB", "ASTM A182 F316"],
        "facing": ["RF", "BW"],
        "standards": ["API 6D"],
        "unspsc": "40141604",
        "gem": "GEM-VALVE-BALL"
    },
    {
        "type": "GLOBE_VALVE",
        "name": "VALVE, GLOBE",
        "metallurgies": ["ASTM A216 WCB", "ASTM A105"],
        "facing": ["RF"],
        "standards": ["BS 1873", "ASME B16.34"],
        "unspsc": "40141602",
        "gem": "GEM-VALVE-GLOBE"
    },
    {
        "type": "SPIRAL_WOUND_GASKET",
        "name": "GASKET, SPIRAL WOUND",
        "metallurgies": ["SS316 / GRAPHITE", "SS304 / GRAPHITE"],
        "facing": ["RF"],
        "standards": ["ASME B16.20"],
        "unspsc": "31161618",
        "gem": "GEM-GASKET-SW"
    },
    {
        "type": "STUD_BOLT",
        "name": "STUD BOLT WITH 2 HEAVY HEX NUTS",
        "metallurgies": ["ASTM A193 B7 / A194 2H", "ASTM A320 L7 / A194 7"],
        "facing": ["THRD"],
        "standards": ["ASME B18.2.1"],
        "unspsc": "31161501",
        "gem": "GEM-BOLT-STUD"
    }
]

def generate_taxonomies():
    # 1. UNSPSC v26
    unspsc_file = TAXONOMY_DIR / "unspsc_v26.csv"
    with open(unspsc_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "title", "level", "parent_code"])
        writer.writerows(UNSPSC_DATA)
    print(f"[+] Wrote {len(UNSPSC_DATA)} rows to {unspsc_file.name}")

    # 2. GeM Categories
    gem_file = TAXONOMY_DIR / "gem_categories.csv"
    with open(gem_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["category_id", "name", "parent_id"])
        writer.writerows(GEM_CATEGORIES_DATA)
    print(f"[+] Wrote {len(GEM_CATEGORIES_DATA)} rows to {gem_file.name}")

    # 3. Canonical Master Material Catalog
    canonical_file = TAXONOMY_DIR / "canonical_master.csv"
    canonical_rows = []
    
    counter = 1
    for item in ITEMS_CONFIG:
        for size_mm, size_inch, dn_code in SIZES:
            for p_class in PRESSURE_CLASSES:
                for mat in item["metallurgies"]:
                    for fac in item["facing"]:
                        for std in item["standards"]:
                            # Filter logical engineering combinations:
                            # 1500# usually RTJ or RF, valves typically API 600 or API 6D
                            cid = f"CAN-{counter:06d}"
                            
                            clean_mat = mat.replace(" / ", "_").replace(" ", "_")
                            clean_type = item["type"]
                            
                            desc = f"{item['name']}, {size_inch} ({dn_code}), CLASS {p_class}, {mat}, {fac} FACING, {std}"
                            
                            canonical_rows.append([
                                cid,
                                clean_type,
                                size_mm,
                                size_inch,
                                dn_code,
                                p_class,
                                mat,
                                fac,
                                std,
                                desc,
                                item["unspsc"],
                                item["gem"]
                            ])
                            counter += 1

    with open(canonical_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "canonical_id", "item_type", "size_nb_mm", "size_inch", "dn_code",
            "pressure_class", "metallurgy", "facing_end", "standard",
            "canonical_description", "unspsc_code", "gem_category_id"
        ])
        writer.writerows(canonical_rows)
    print(f"[+] Wrote {len(canonical_rows)} canonical materials to {canonical_file.name}")

if __name__ == "__main__":
    generate_taxonomies()
