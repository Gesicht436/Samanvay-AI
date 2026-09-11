"""
generate_catalogs.py
Generates 10,000+ realistic synthetic CPSE inventory catalogs across IOCL, ONGC, and BPCL.
Implements distinct enterprise dialect noising profiles and inventory metadata.
Author: Data Pipelines & Taxonomy Lead (Shaurya)
"""

import os
import csv
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
TAXONOMY_DIR = DATA_DIR / "taxonomies"
OUTPUT_DIR = DATA_DIR / "mock_cpes_catalogs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)

DEPOTS = {
    "IOCL": [
        ("DEPOT-IOCL-PNP", "Panipat Refinery, Haryana"),
        ("DEPOT-IOCL-MTH", "Mathura Refinery, Uttar Pradesh"),
        ("DEPOT-IOCL-GWT", "Guwahati Refinery, Assam"),
        ("DEPOT-IOCL-KYL", "Koyali Refinery, Gujarat"),
        ("DEPOT-IOCL-PRD", "Paradip Refinery, Odisha"),
    ],
    "ONGC": [
        ("DEPOT-ONGC-HZR", "Hazira Gas Processing Plant, Gujarat"),
        ("DEPOT-ONGC-URN", "Uran Plant, Maharashtra"),
        ("DEPOT-ONGC-ANK", "Ankleshwar Asset, Gujarat"),
        ("DEPOT-ONGC-MBO", "Mumbai Offshore Logistics Base, Maharashtra"),
        ("DEPOT-ONGC-RJM", "Rajahmundry Asset, Andhra Pradesh"),
    ],
    "BPCL": [
        ("DEPOT-BPCL-MUM", "Mumbai Refinery, Mahul, Maharashtra"),
        ("DEPOT-BPCL-KCH", "Kochi Refinery, Kerala"),
        ("DEPOT-BPCL-BIN", "Bina Refinery, Madhya Pradesh"),
        ("DEPOT-BPCL-NML", "Numaligarh Depot Base, Assam"),
    ]
}

def load_canonical_master():
    canonical_file = TAXONOMY_DIR / "canonical_master.csv"
    if not canonical_file.exists():
        raise FileNotFoundError(f"Missing {canonical_file}. Run curate_taxonomies.py first.")
    
    items = []
    with open(canonical_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(row)
    return items

def to_iocl_dialect(item):
    """
    IOCL Profile: Heavy truncation, drops vowels, spaces stripped, imperial units preferred.
    e.g., FLG WNRF 4IN 300# A105, VLV GT 2IN 150LB WCB
    """
    type_map = {
        "FLANGE_WELD_NECK": "FLG WN",
        "FLANGE_BLIND": "FLG BLD",
        "FLANGE_SLIP_ON": "FLG SO",
        "GATE_VALVE": "VLV GT",
        "BALL_VALVE": "VLV BL",
        "GLOBE_VALVE": "VLV GLB",
        "SPIRAL_WOUND_GASKET": "GSKT SPWD",
        "STUD_BOLT": "STUDBLT"
    }
    
    t_str = type_map.get(item["item_type"], item["item_type"])
    
    # Pressure representation
    p_choice = random.choice([f"{item['pressure_class']}#", f"{item['pressure_class']}LB", f"CL{item['pressure_class']}"])
    
    # Size representation
    s_inch = item["size_inch"].replace('"', 'IN')
    
    # Metallurgy abbreviation
    mat_map = {
        "ASTM A105": "A105",
        "ASTM A350 LF2": "A350-LF2",
        "ASTM A182 F304": "SS304",
        "ASTM A182 F316": "SS316",
        "ASTM A216 WCB": "WCB",
        "SS316 / GRAPHITE": "SS316/GRAF",
        "SS304 / GRAPHITE": "SS304/GRAF",
        "ASTM A193 B7 / A194 2H": "B7/2H",
        "ASTM A320 L7 / A194 7": "L7/GR7"
    }
    m_str = mat_map.get(item["metallurgy"], item["metallurgy"].replace("ASTM ", ""))
    
    facing = item["facing_end"]
    if facing == "RF" and "FLG WN" in t_str and random.random() < 0.6:
        t_str = "FLG WNRF"
        facing = ""
    elif facing == "RTJ" and "FLG" in t_str and random.random() < 0.5:
        t_str = t_str + " RTJ"
        facing = ""
        
    parts = [t_str, s_inch, p_choice, m_str]
    if facing:
        parts.append(facing)
    if random.random() < 0.4:
        parts.append(item["standard"].replace(" ", ""))
        
    return " ".join([p for p in parts if p]).strip()

def to_ongc_dialect(item):
    """
    ONGC Profile: Verbose, comma-delimited, formal punctuation, exact standards.
    e.g., FLANGE, WELDING NECK, 4 INCH, CLASS 300, ASTM A105, ASME B16.5, RF
    """
    type_map = {
        "FLANGE_WELD_NECK": "FLANGE, WELDING NECK",
        "FLANGE_BLIND": "FLANGE, BLIND",
        "FLANGE_SLIP_ON": "FLANGE, SLIP-ON",
        "GATE_VALVE": "VALVE, GATE",
        "BALL_VALVE": "VALVE, BALL",
        "GLOBE_VALVE": "VALVE, GLOBE",
        "SPIRAL_WOUND_GASKET": "GASKET, SPIRAL WOUND",
        "STUD_BOLT": "STUD BOLT WITH NUTS"
    }
    t_str = type_map.get(item["item_type"], item["item_type"])
    
    s_inch = item["size_inch"].replace('"', ' INCH')
    p_str = f"CLASS {item['pressure_class']}"
    m_str = item["metallurgy"]
    std_str = item["standard"]
    fac_str = f"{item['facing_end']} FACING"
    
    parts = [t_str, s_inch, p_str, m_str, std_str, fac_str]
    return ", ".join(parts)

def to_bpcl_dialect(item):
    """
    BPCL Profile: Metric-preferred, hyphenated, compact alphanumeric standard.
    e.g., FLG-WN-DN100-PN50-A105-RF, VLV-GT-DN50-CL150-WCB-BW
    """
    type_map = {
        "FLANGE_WELD_NECK": "FLG-WN",
        "FLANGE_BLIND": "FLG-BLD",
        "FLANGE_SLIP_ON": "FLG-SO",
        "GATE_VALVE": "VLV-GT",
        "BALL_VALVE": "VLV-BL",
        "GLOBE_VALVE": "VLV-GL",
        "SPIRAL_WOUND_GASKET": "GSKT-SW",
        "STUD_BOLT": "BLT-STUD"
    }
    t_str = type_map.get(item["item_type"], item["item_type"])
    
    # Metric pressure code PN roughly: 150->PN20, 300->PN50, 600->PN100, 900->PN150, 1500->PN250
    pn_map = {150: "PN20", 300: "PN50", 600: "PN100", 900: "PN150", 1500: "PN250"}
    p_str = pn_map.get(int(item["pressure_class"]), f"CL{item['pressure_class']}")
    if random.random() < 0.4:
        p_str = f"CL{item['pressure_class']}"
        
    mat_map = {
        "ASTM A105": "A105",
        "ASTM A350 LF2": "A350LF2",
        "ASTM A182 F304": "SS304",
        "ASTM A182 F316": "SS316",
        "ASTM A216 WCB": "WCB",
        "SS316 / GRAPHITE": "SS316-GR",
        "SS304 / GRAPHITE": "SS304-GR",
        "ASTM A193 B7 / A194 2H": "B7-2H",
        "ASTM A320 L7 / A194 7": "L7-GR7"
    }
    m_str = mat_map.get(item["metallurgy"], item["metallurgy"].replace("ASTM ", "").replace(" ", ""))
    
    dn_code = item["dn_code"]
    facing = item["facing_end"]
    
    return f"{t_str}-{dn_code}-{p_str}-{m_str}-{facing}"

def estimate_cost(item_type, size_mm, p_class, mat):
    size_factor = (float(size_mm) / 25.0) ** 1.3
    class_factor = (float(p_class) / 150.0) ** 0.8
    mat_mult = 1.0
    if "316" in mat:
        mat_mult = 3.2
    elif "304" in mat:
        mat_mult = 2.4
    elif "LF2" in mat or "L7" in mat:
        mat_mult = 1.6
        
    base_costs = {
        "FLANGE_WELD_NECK": 2200,
        "FLANGE_BLIND": 1800,
        "FLANGE_SLIP_ON": 1600,
        "GATE_VALVE": 18000,
        "BALL_VALVE": 22000,
        "GLOBE_VALVE": 24000,
        "SPIRAL_WOUND_GASKET": 650,
        "STUD_BOLT": 350
    }
    base = base_costs.get(item_type, 2000)
    cost = int(base * size_factor * class_factor * mat_mult)
    return max(150, (cost // 10) * 10)

def generate_catalogs():
    canonical_items = load_canonical_master()
    print(f"Loaded {len(canonical_items)} canonical items for catalog generation.")
    
    # We will generate ~3,500 items per CPSE (~10,500 total)
    cpse_configs = [
        ("IOCL", to_iocl_dialect, "IOCL-MM-", 3600),
        ("ONGC", to_ongc_dialect, "ONGC-MAT-", 3600),
        ("BPCL", to_bpcl_dialect, "BPCL-SAP-", 3600),
    ]
    
    for cpse, dialect_fn, prefix, target_count in cpse_configs:
        rows = []
        depots_pool = DEPOTS[cpse]
        
        # Ensure high overlap: sample from canonical items with replacement
        sampled_items = random.choices(canonical_items, k=target_count)
        
        for i, item in enumerate(sampled_items, 1):
            local_code = f"{prefix}{i:07d}"
            raw_desc = dialect_fn(item)
            depot_id, depot_loc = random.choice(depots_pool)
            
            # Stock simulation:
            # 25% items have zero stock (actively procuring)
            # 50% items have healthy stock
            # 25% items have high idle surplus stock (>180 days idle)
            stock_scenario = random.random()
            if stock_scenario < 0.25:
                quantity = 0
                idle_days = 0
            elif stock_scenario < 0.70:
                quantity = random.randint(5, 50)
                idle_days = random.randint(10, 120)
            else:
                quantity = random.randint(20, 150)
                idle_days = random.randint(180, 750) # High surplus!
                
            unit_cost = estimate_cost(
                item["item_type"], 
                item["size_nb_mm"], 
                item["pressure_class"], 
                item["metallurgy"]
            )
            
            rows.append({
                "local_code": local_code,
                "cpse": cpse,
                "raw_description": raw_desc,
                "canonical_id": item["canonical_id"],
                "depot_id": depot_id,
                "depot_location": depot_loc,
                "quantity": quantity,
                "unit_cost_inr": unit_cost,
                "idle_days": idle_days,
                "extracted_item_type": item["item_type"],
                "extracted_size_nb_mm": item["size_nb_mm"],
                "extracted_pressure_class": item["pressure_class"],
                "extracted_metallurgy": item["metallurgy"],
                "extracted_facing": item["facing_end"],
                "extracted_standard": item["standard"]
            })
            
        out_csv = OUTPUT_DIR / f"{cpse.lower()}_materials.csv"
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
            
        print(f"[+] Wrote {len(rows)} records to {out_csv.name}")

if __name__ == "__main__":
    generate_catalogs()
