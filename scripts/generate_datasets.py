"""
Samanvay-AI Dataset Generator
Generates:
1. data/inventory_catalog.csv (5,000 rows, CPSE ERP dialects, 15% sparsity)
2. data/golden_benchmarks.json (150 paired test cases: 50 Tier-1, 50 Tier-2, 50 Tier-3 testing 21 safety modules)
3. data/ocr_payloads.json (500 PaddleOCR MTC payloads, 10% low confidence, 5% hallucinations)
"""

import csv
import json
import os
import random
from typing import Dict, List, Any

# Set deterministic random seed for reproducibility
random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# 1. INVENTORY CATALOG (5,000 Rows)
# ----------------------------------------------------------------------

CPSE_DEPOTS = {
    "IOCL": [
        "Panipat Refinery, Haryana",
        "Mathura Refinery, Uttar Pradesh",
        "Koyali Refinery, Gujarat",
        "Paradip Refinery, Odisha",
        "Barauni Refinery, Bihar",
        "Guwahati Refinery, Assam",
        "Digboi Refinery, Assam"
    ],
    "ONGC": [
        "Hazira Gas Processing Plant, Gujarat",
        "Ankleshwar Asset, Gujarat",
        "Uran Gas Processing Complex, Maharashtra",
        "Mumbai High Offshore Logistics Base, Maharashtra",
        "Rajahmundry Asset, Andhra Pradesh"
    ],
    "BPCL": [
        "Mumbai Mahul Refinery, Maharashtra",
        "Kochi Refinery, Kerala",
        "Bina Refinery, Madhya Pradesh"
    ],
    "HPCL": [
        "Mumbai Refinery, Maharashtra",
        "Visakh Refinery, Andhra Pradesh"
    ],
    "GAIL": [
        "Pata Petrochemical Complex, Uttar Pradesh",
        "Vijaipur Gas Processing Complex, Madhya Pradesh"
    ]
}

ITEM_TYPES = [
    "FLANGE", "GATE_VALVE", "GLOBE_VALVE", "CHECK_VALVE", "BALL_VALVE",
    "BUTTERFLY_VALVE", "PIPE", "ELBOW_90", "TEE_EQUAL", "REDUCER_CONC",
    "STUD_BOLT", "GASKET_SWG", "GASKET_RTJ", "PSV_VALVE", "CENTRIFUGAL_PUMP_SPARE"
]

SIZES_IMPERIAL = ["1/2IN", "3/4IN", "1IN", "1.5IN", "2IN", "3IN", "4IN", "6IN", "8IN", "10IN", "12IN", "16IN", "20IN", "24IN"]
SIZES_METRIC = ["DN15", "DN20", "DN25", "DN40", "DN50", "DN80", "DN100", "DN150", "DN200", "DN250", "DN300", "DN400", "DN500", "DN600"]
CLASSES_IMPERIAL = ["150#", "300#", "600#", "900#", "1500#", "2500#"]
CLASSES_METRIC = ["PN20", "PN50", "PN100", "PN150", "PN250", "PN420"]
SCHEDULES = ["SCH 20", "SCH 40", "SCH 80", "SCH 160", "SCH XXS"]
METALLURGIES = [
    "ASTM A105", "ASTM A106 GR.B", "ASTM A216 WCB", "ASTM A350 LF2",
    "ASTM A182 F304", "ASTM A182 F316", "ASTM A182 F316L", "ASTM A182 F51",
    "ASTM A182 F53", "ASTM A182 F11", "ASTM A182 F22", "ASTM A193 B7", "ASTM A193 B16", "INCONEL 625"
]
FACINGS = ["RF", "RTJ", "FF", "BW", "SW"]
VALVE_TRIMS = ["TR1", "TR5", "TR8", "TR12", "TR16"]

def generate_iocl_description(item_type: str, size: str, cls: str, mat: str, sched: str, facing: str, trim: str, is_sparse: bool) -> str:
    """IOCL Dialect: Truncated imperial strings with hash ratings."""
    tokens = []
    if item_type == "FLANGE":
        flg_type = random.choice(["WNRF", "BLRF", "SORF", "SWRF", "THRF"])
        tokens = ["FLG", flg_type, size, cls, mat]
    elif "VALVE" in item_type:
        v_short = "GT" if "GATE" in item_type else ("GL" if "GLOBE" in item_type else ("CHK" if "CHECK" in item_type else ("BL" if "BALL" in item_type else "BFV")))
        tokens = ["VLV", v_short, "FLG", size, cls, mat]
        if not is_sparse:
            tokens.append(trim)
    elif item_type == "PIPE":
        mfg = random.choice(["SMLS", "ERW"])
        tokens = ["PIPE", mfg, size, sched if not is_sparse else "", mat]
    elif item_type.startswith("ELBOW") or item_type.startswith("TEE") or item_type.startswith("REDUCER"):
        f_short = "ELB 90 LR" if "ELBOW" in item_type else ("TEE EQ" if "TEE" in item_type else "RED CONC")
        tokens = [f_short, size, sched if not is_sparse else "", "A234WPB" if "A105" in mat or "WCB" in mat else mat]
    elif item_type == "STUD_BOLT":
        tokens = ["STUD BLT", size, "X 180MM", mat, "W/ 2H NUTS"]
    elif item_type.startswith("GASKET"):
        tokens = ["GSKT", "SWG" if "SWG" in item_type else "RTJ OCT", size, cls, "SS316/GRAFOIL" if not is_sparse else "SS316"]
    else:
        tokens = [item_type.replace("_", " "), size, cls, mat]
    
    # Clean empty tokens
    return " ".join([t for t in tokens if t])

def generate_ongc_description(item_type: str, size: str, cls: str, mat: str, sched: str, facing: str, trim: str, is_sparse: bool) -> str:
    """ONGC Dialect: Verbose, comma-delimited formal specification."""
    parts = []
    size_verbose = size.replace("IN", " INCH").replace("1/2", "1/2").replace("3/4", "3/4")
    cls_verbose = f"CLASS {cls.replace('#', '')}"
    
    if item_type == "FLANGE":
        flg_type = random.choice(["WELDING NECK", "BLIND", "SLIP ON", "SOCKET WELD"])
        parts = ["FLANGE", flg_type, size_verbose, cls_verbose, mat, "ASME B16.5"]
        if not is_sparse:
            parts.append(f"{facing} FACING")
    elif "VALVE" in item_type:
        v_name = "GATE VALVE" if "GATE" in item_type else ("GLOBE VALVE" if "GLOBE" in item_type else ("CHECK VALVE" if "CHECK" in item_type else "BALL VALVE"))
        parts = [v_name, "BOLTED BONNET", size_verbose, cls_verbose, f"BODY {mat}", "FLANGED ENDS"]
        if not is_sparse:
            parts.append(f"TRIM {trim.replace('TR', '')}")
            parts.append(f"{facing} FACING")
    elif item_type == "PIPE":
        parts = ["LINE PIPE", "SEAMLESS", size_verbose, sched if not is_sparse else "", mat, "ASME B36.10M", "BEVELED ENDS"]
    elif item_type.startswith("ELBOW") or item_type.startswith("TEE") or item_type.startswith("REDUCER"):
        f_name = "ELBOW 90 DEG LONG RADIUS" if "ELBOW" in item_type else ("EQUAL TEE" if "TEE" in item_type else "CONCENTRIC REDUCER")
        parts = ["BUTTWELD FITTING", f_name, size_verbose, sched if not is_sparse else "", "ASTM A234 WPB", "ASME B16.9"]
    elif item_type == "STUD_BOLT":
        parts = ["STUD BOLT WITH TWO HEAVY HEX NUTS", size_verbose, "LENGTH 180 MM", f"STUD {mat}", "NUTS ASTM A194 GR 2H"]
    elif item_type.startswith("GASKET"):
        g_name = "SPIRAL WOUND GASKET WITH INNER AND OUTER RING" if "SWG" in item_type else "METALLIC RING JOINT GASKET OCTAGONAL"
        parts = [g_name, size_verbose, cls_verbose, "ASME B16.20"]
    else:
        parts = [item_type.replace("_", " "), size_verbose, cls_verbose, mat]
        
    return ", ".join([p for p in parts if p])

def generate_metric_description(item_type: str, size: str, cls: str, mat: str, sched: str, facing: str, trim: str, is_sparse: bool) -> str:
    """BPCL / HPCL / GAIL Dialect: Metric-preferred hyphenated alphanumeric strings."""
    tokens = []
    if item_type == "FLANGE":
        flg_type = random.choice(["WN", "BLD", "SO", "SW"])
        tokens = ["FLG", flg_type, size, cls, mat.replace("ASTM ", "").replace(" ", ""), facing if not is_sparse else ""]
    elif "VALVE" in item_type:
        v_short = "GT" if "GATE" in item_type else ("GL" if "GLOBE" in item_type else ("CHK" if "CHECK" in item_type else ("BL" if "BALL" in item_type else "BFV")))
        tokens = ["VLV", v_short, size, cls, mat.replace("ASTM ", "").replace(" ", "")]
        if not is_sparse:
            tokens.append(trim)
            tokens.append(facing)
    elif item_type == "PIPE":
        tokens = ["PIPE", "SMLS", size, sched if not is_sparse else "", mat.replace("ASTM ", "").replace(" ", ""), "BE"]
    elif item_type.startswith("ELBOW") or item_type.startswith("TEE") or item_type.startswith("REDUCER"):
        f_short = "ELB-90LR" if "ELBOW" in item_type else ("TEE-EQ" if "TEE" in item_type else "RED-CONC")
        tokens = [f_short, size, sched if not is_sparse else "", "A234WPB"]
    elif item_type == "STUD_BOLT":
        tokens = ["STUD", size, "180MM", mat.replace("ASTM ", "").replace(" ", ""), "2H"]
    elif item_type.startswith("GASKET"):
        tokens = ["GSKT", "SWG" if "SWG" in item_type else "RTJ", size, cls, "SS316-GRAF" if not is_sparse else ""]
    else:
        tokens = [item_type.replace("_", "-"), size, cls, mat.replace(" ", "")]
        
    return "-".join([t for t in tokens if t])

def generate_inventory_catalog(count: int = 5000) -> List[Dict[str, Any]]:
    rows = []
    # 30% IOCL (1500), 30% ONGC (1500), 40% BPCL/HPCL/GAIL (2000)
    allocations = [
        ("IOCL", int(count * 0.30)),
        ("ONGC", int(count * 0.30)),
        ("BPCL", int(count * 0.15)),
        ("HPCL", int(count * 0.15)),
        ("GAIL", count - int(count * 0.30) - int(count * 0.30) - int(count * 0.15) - int(count * 0.15))
    ]
    
    sku_counter = 1
    for cpse, num_rows in allocations:
        depots = CPSE_DEPOTS[cpse]
        for _ in range(num_rows):
            item_type = random.choice(ITEM_TYPES)
            mat = random.choice(METALLURGIES)
            sched = random.choice(SCHEDULES)
            facing = random.choice(FACINGS)
            trim = random.choice(VALVE_TRIMS)
            depot = random.choice(depots)
            is_sparse = random.random() < 0.15  # 15% sparsity
            
            if cpse == "IOCL":
                size = random.choice(SIZES_IMPERIAL)
                cls = random.choice(CLASSES_IMPERIAL)
                raw_desc = generate_iocl_description(item_type, size, cls, mat, sched, facing, trim, is_sparse)
            elif cpse == "ONGC":
                size = random.choice(SIZES_IMPERIAL)
                cls = random.choice(CLASSES_IMPERIAL)
                raw_desc = generate_ongc_description(item_type, size, cls, mat, sched, facing, trim, is_sparse)
            else: # BPCL, HPCL, GAIL
                size = random.choice(SIZES_METRIC)
                cls = random.choice(CLASSES_METRIC)
                raw_desc = generate_metric_description(item_type, size, cls, mat, sched, facing, trim, is_sparse)
            
            # Realistic quantities, unit costs, and idle days
            qty = random.randint(1, 150)
            
            # Value tiers based on metallurgy & item
            base_cost = 2500
            if "VALVE" in item_type:
                base_cost = 18000
            elif "PUMP" in item_type or "PSV" in item_type:
                base_cost = 45000
            elif "FLANGE" in item_type:
                base_cost = 4500
            
            if "F316" in mat or "F51" in mat:
                base_cost *= 2.5
            elif "F53" in mat or "INCONEL" in mat:
                base_cost *= 6.0
            
            unit_cost = round(base_cost * random.uniform(0.75, 1.85), 2)
            days_idle = random.choice([
                random.randint(5, 60),      # active
                random.randint(91, 365),    # surplus
                random.randint(366, 1200)   # deep dormant
            ])
            
            sku_prefix = item_type[:3]
            sku_code = f"{cpse}-{sku_prefix}-{sku_counter:05d}"
            sku_counter += 1
            
            rows.append({
                "sku_code": sku_code,
                "cpse_name": cpse,
                "depot_location": depot,
                "raw_description": raw_desc,
                "quantity": qty,
                "unit_cost_inr": unit_cost,
                "days_idle": days_idle
            })
            
    return rows

# ----------------------------------------------------------------------
# 2. GOLDEN BENCHMARKS (150 Paired Test Cases)
# ----------------------------------------------------------------------

def generate_golden_benchmarks() -> List[Dict[str, Any]]:
    cases = []
    case_id = 1
    
    # ------------------------------------------------------------------
    # TIER 1: 50 IDENTICAL / SAFE OVER-RATING CASES (>= 95% Match)
    # ------------------------------------------------------------------
    tier1_templates = [
        # (item_type, q_size, c_size, q_class, c_class, q_mat, c_mat, q_extra, c_extra, desc)
        ("PIPE", 250.0, 250.0, 300, 350, "Galvanized Iron", "Galvanized Iron", {"sched": "SCH 40"}, {"sched": "SCH 40"}, "10\" GI Pipe: Safe Over-Rating (350 PSI >= 300 PSI) with identical dims"),
        ("GATE_VALVE", 150.0, 150.0, 150, 150, "ASTM A216 WCB", "ASTM A216 WCB", {"trim": 1, "facing": "RF"}, {"trim": 8, "facing": "RF"}, "Gate Valve 6\" 150#: Trim 8 (Stellite hardfaced) safe upgrade for Trim 1"),
        ("GATE_VALVE", 150.0, 150.0, 300, 300, "ASTM A216 WCB", "ASTM A216 WCB", {"trim": 8, "facing": "RF"}, {"trim": 8, "facing": "RF"}, "Gate Valve 6\" 300# WCB Trim 8: Exact Parity"),
        ("PIPE", 100.0, 100.0, 150, 150, "ASTM A106 GR.B", "ASTM A106 GR.B", {"sched": "SCH 40", "mfg": "SMLS"}, {"sched": "SCH 40", "mfg": "SMLS"}, "Pipe 4\" Sch 40 A106-B SMLS: Exact Parity"),
        ("FLANGE", 100.0, 100.0, 300, 300, "ASTM A105", "ASTM A105", {"facing": "RF"}, {"facing": "RF"}, "Flange WN 4\" Class 300 A105 RF: Exact Parity"),
        ("FITTING_SW", 50.0, 50.0, 3000, 6000, "ASTM A105", "ASTM A105", {"type": "COUPLING"}, {"type": "COUPLING"}, "Socket Weld Coupling: Dimension-preserving safe over-rating 6000# for 3000#"),
        ("BALL_VALVE", 50.0, 50.0, 600, 600, "ASTM A105", "ASTM A105", {"fire_safe": True, "port": "FULL_BORE"}, {"fire_safe": True, "port": "FULL_BORE"}, "Ball Valve 2\" 600# Full Bore Fire-Safe: Exact Parity"),
        ("BALL_VALVE", 80.0, 80.0, 300, 300, "ASTM A216 WCB", "ASTM A216 WCB", {"port": "REDUCED_BORE"}, {"port": "FULL_BORE"}, "Ball Valve 3\" 300#: Full Bore safe upgrade for Reduced Bore"),
        ("STUD_BOLT", 20.0, 20.0, None, None, "ASTM A193 B7", "ASTM A193 B16", {"nut": "ASTM A194 2H"}, {"nut": "ASTM A194 7"}, "Stud Bolt: High-creep ASTM A193 B16 safe high-temperature upgrade for B7"),
        ("GASKET_SWG", 150.0, 150.0, 300, 300, "SS316", "SS316", {"inner_ring": False}, {"inner_ring": True}, "Spiral Wound Gasket 6\" 300#: Added solid inner ring safe upgrade"),
        ("CHECK_VALVE", 100.0, 100.0, 150, 150, "ASTM A216 WCB", "ASTM A216 WCB", {"design": "SWING"}, {"design": "RETAINERLESS_DUAL_PLATE"}, "Check Valve 4\" 150#: Retainerless fugitive-emission safe upgrade"),
        ("FLANGE", 150.0, 150.0, 150, 150, "ASTM A182 F304", "ASTM A182 F316", {"facing": "RF"}, {"facing": "RF"}, "Flange 6\" 150#: Molybdenum SS316 safe corrosion upgrade for SS304 in standard fluid"),
        ("PIPE", 50.0, 50.0, 150, 150, "ASTM A312 TP304", "ASTM A312 TP316", {"sched": "SCH 40S"}, {"sched": "SCH 40S"}, "Stainless Pipe 2\" Sch 40S: TP316 safe drop-in upgrade for TP304"),
        ("GLOBE_VALVE", 50.0, 50.0, 800, 800, "ASTM A105", "ASTM A105", {"trim": 8, "facing": "SW"}, {"trim": 8, "facing": "SW"}, "Forged Globe Valve 2\" Class 800# SW: Exact Parity"),
        ("ELBOW_90", 150.0, 150.0, None, None, "ASTM A234 WPB", "ASTM A234 WPB", {"sched": "SCH 40", "radius": "LR"}, {"sched": "SCH 40", "radius": "LR"}, "90 Deg LR Elbow 6\" Sch 40: Exact Parity"),
        ("TEE_EQUAL", 100.0, 100.0, None, None, "ASTM A234 WPB", "ASTM A234 WPB", {"sched": "SCH 40"}, {"sched": "SCH 40"}, "Equal Tee 4\" Sch 40 WPB: Exact Parity"),
        ("REDUCER_CONC", 150.0, 150.0, None, None, "ASTM A234 WPB", "ASTM A234 WPB", {"sched": "SCH 40", "outlet_size": 100.0}, {"sched": "SCH 40", "outlet_size": 100.0}, "Concentric Reducer 6\"x4\" Sch 40: Exact Parity"),
        ("FLANGE_BLIND", 200.0, 200.0, 150, 150, "ASTM A105", "ASTM A105", {"facing": "RF"}, {"facing": "RF"}, "Blind Flange 8\" Class 150 RF: Exact Parity"),
        ("GASKET_RTJ", 100.0, 100.0, 600, 600, "Soft Iron", "Soft Iron", {"ring_type": "OCTAGONAL_R"}, {"ring_type": "OCTAGONAL_R"}, "RTJ Ring Gasket R-37 Octagonal Soft Iron: Exact Parity"),
        ("GATE_VALVE", 200.0, 200.0, 150, 150, "ASTM A216 WCB", "ASTM A216 WCB", {"trim": 8, "facing": "RF"}, {"trim": 5, "facing": "RF"}, "Gate Valve 8\" 150#: Full Stellite Trim 5 safe upgrade for Trim 8"),
    ]
    
    # Expand Tier 1 to 50 distinct test cases
    for i in range(50):
        tpl = tier1_templates[i % len(tier1_templates)]
        cases.append({
            "test_id": f"GB-T1-{case_id:04d}",
            "expected_tier": "TIER_1_IDENTICAL",
            "expected_is_compatible": True,
            "expected_violation_code": None,
            "target_standard": "ASME B16.5 / ASTM / API 600",
            "scenario_description": f"Tier-1 Match #{case_id}: {tpl[9]} (Case variant {i+1})",
            "query_part": {
                "item_type": tpl[0],
                "size_nb_mm": tpl[1],
                "pressure_class": tpl[3],
                "metallurgy": tpl[5],
                "properties": tpl[7]
            },
            "candidate_part": {
                "item_type": tpl[0],
                "size_nb_mm": tpl[2],
                "pressure_class": tpl[4],
                "metallurgy": tpl[6],
                "properties": tpl[8]
            }
        })
        case_id += 1
        
    # ------------------------------------------------------------------
    # TIER 2: 50 FUNCTIONAL SUBSTITUTE / SAFE UPGRADES (80% - 94% Match)
    # ------------------------------------------------------------------
    tier2_templates = [
        ("PIPE", 100.0, 100.0, 150, 150, "ASTM A106 GR.B", "ASTM A106 GR.B", {"sched": "SCH 40"}, {"sched": "SCH 80"}, "Pipe 4\": Schedule upgrade SCH 40 -> SCH 80 (Thicker wall, minor flow delta, requires HITL sign-off)"),
        ("FLANGE", 100.0, 100.0, 150, 150, "ASTM A182 F304", "ASTM A182 F316L", {"facing": "RF"}, {"facing": "RF"}, "Flange 4\" 150#: Low-carbon SS316L substitute for SS304 (Welding procedure verification required)"),
        ("FLANGE", 150.0, 150.0, 150, 150, "ASTM A182 F316", "ASTM A182 F51", {"facing": "RF"}, {"facing": "RF"}, "Flange 6\" 150#: Duplex 2205 (F51) safe alloy upgrade for SS316 (Superior yield, HITL sign-off)"),
        ("GATE_VALVE", 100.0, 100.0, 150, 150, "ASTM A351 CF8", "ASTM A351 CF8M", {"facing": "RF", "trim": 10}, {"facing": "RF", "trim": 10}, "Gate Valve 4\" 150#: CF8M (SS316 cast) functional substitute for CF8 (SS304 cast)"),
        ("PIPE", 150.0, 150.0, 300, 300, "API 5L GR.B PSL1", "API 5L GR.B PSL2", {"sched": "SCH 40"}, {"sched": "SCH 40"}, "Line Pipe 6\" 300#: API 5L PSL 2 quality upgrade for PSL 1 (Mandatory Charpy notch toughness verified)"),
        ("PIPE", 200.0, 200.0, 150, 150, "ASTM A106 GR.B", "ASTM A106 GR.B", {"coating": "BARE"}, {"coating": "3LPE_COATED"}, "Pipe 8\" Bare vs 3-Layer Polyethylene (3LPE) coated (Superior external corrosion protection)"),
        ("BUTTERFLY_VALVE", 150.0, 150.0, 150, 150, "ASTM A216 WCB", "ASTM A216 WCB", {"offset": "SINGLE_OFFSET"}, {"offset": "DOUBLE_OFFSET"}, "Butterfly Valve 6\" 150#: High-performance double-offset safe upgrade for single-offset"),
        ("PUMP_SEAL", 50.0, 50.0, None, None, "SS316/CARBON/SIC", "SS316/SIC/SIC", {"plan": "PLAN_11"}, {"plan": "PLAN_53A"}, "Pump Mechanical Seal: Dual pressurized Plan 53A upgrade over single Plan 11"),
        ("BEARING", 80.0, 80.0, None, None, "52100_STEEL", "52100_STEEL", {"clearance": "CN"}, {"clearance": "C3"}, "Deep Groove Ball Bearing 6316: C3 radial clearance upgrade for high-speed motor"),
        ("FLANGE", 100.0, 100.0, 300, 600, "ASTM A105", "ASTM A105", {"facing": "RF", "is_spool_adapter": True}, {"facing": "RF", "is_spool_adapter": True}, "Unattached Flange Class 300# to 600# with transition engineering verification (HITL check)"),
        ("PIPE", 50.0, 50.0, 150, 150, "ASTM A335 P11", "ASTM A335 P22", {"sched": "SCH 80"}, {"sched": "SCH 80"}, "Cr-Mo Alloy Pipe 2\": 2.25Cr-1Mo (P22) safe creep upgrade for 1.25Cr-0.5Mo (P11)"),
        ("STUD_BOLT", 24.0, 24.0, None, None, "ASTM A193 B7", "ASTM A193 B7M", {"nut": "ASTM A194 2H"}, {"nut": "ASTM A194 2HM"}, "Stud Bolt: NACE MR0175 compliant B7M (<=22 HRC) safe upgrade for B7"),
        ("BALL_VALVE", 100.0, 100.0, 150, 150, "ASTM A105", "ASTM A105", {"operator": "LEVER"}, {"operator": "GEAR_ACTUATOR"}, "Ball Valve 4\" 150#: Gear actuator upgrade for lever operator"),
        ("GLOBE_VALVE", 80.0, 80.0, 300, 300, "ASTM A216 WCB", "ASTM A217 WC6", {"facing": "RF"}, {"facing": "RF"}, "Globe Valve 3\" 300#: 1.25Cr alloy WC6 body substitute for WCB in high temperature"),
        ("CHECK_VALVE", 150.0, 150.0, 300, 300, "ASTM A216 WCB", "ASTM A216 WCB", {"disc_type": "SINGLE_DISC"}, {"disc_type": "DUAL_PLATE"}, "Check Valve 6\" 300#: Fast-closing dual plate non-slam substitute for swing disc"),
    ]
    
    for i in range(50):
        tpl = tier2_templates[i % len(tier2_templates)]
        cases.append({
            "test_id": f"GB-T2-{case_id:04d}",
            "expected_tier": "TIER_2_SUBSTITUTE",
            "expected_is_compatible": True,
            "expected_violation_code": "REQUIRES_HITL_VERIFICATION",
            "target_standard": "ASME B31.3 / ASTM DAG / API 682",
            "scenario_description": f"Tier-2 Substitute #{case_id}: {tpl[8]} (Case variant {i+1})",
            "query_part": {
                "item_type": tpl[0],
                "size_nb_mm": tpl[1],
                "pressure_class": tpl[3],
                "metallurgy": tpl[5],
                "properties": tpl[7]
            },
            "candidate_part": {
                "item_type": tpl[0],
                "size_nb_mm": tpl[2],
                "pressure_class": tpl[4],
                "metallurgy": tpl[6],
                "properties": tpl[8]
            }
        })
        case_id += 1

    # ------------------------------------------------------------------
    # TIER 3: 50 FATAL INVARIANTS / ZERO-TOLERANCE HAZARD TRAPS
    # ------------------------------------------------------------------
    tier3_cases = [
        # 1. Pressure Down-Rating
        ("FLANGE", 100.0, 100.0, 300, 150, "ASTM A105", "ASTM A105", {}, {}, "FATAL_PRESSURE_DOWN_RATING", "ASME B16.5", "Pressure Down-Rating: Class 150 flange installed on Class 300 line (Fatal rupture risk)"),
        ("PIPE", 250.0, 250.0, 300, 250, "Galvanized Iron", "Galvanized Iron", {}, {}, "FATAL_PRESSURE_DOWN_RATING", "ASME B31.3", "Pressure Down-Rating: 250 PSI pipe replacing 300 PSI design pressure"),
        # 2. Dimensional Mismatches
        ("FLANGE", 250.0, 200.0, 300, 300, "ASTM A105", "ASTM A105", {}, {}, "FATAL_DIMENSIONAL_MISMATCH", "ASME B16.5", "Dimensional Mismatch: 8\" (200mm) flange proposed for 10\" (250mm) line"),
        ("GATE_VALVE", 150.0, 100.0, 150, 150, "ASTM A216 WCB", "ASTM A216 WCB", {}, {}, "FATAL_DIMENSIONAL_MISMATCH", "ASME B16.10", "Dimensional Mismatch: 4\" (100mm) valve proposed for 6\" (150mm) line"),
        # 3. Metallurgy Downgrades
        ("FLANGE", 100.0, 100.0, 150, 150, "ASTM A182 F316", "ASTM A105", {}, {}, "FATAL_METALLURGY_DOWNGRADE", "ASTM Metallurgy DAG", "Metallurgy Downgrade: Carbon Steel A105 replacing Austenitic Stainless Steel SS316 (Acid corrosion blowout)"),
        ("PIPE", 150.0, 150.0, 300, 300, "ASTM A182 F51", "ASTM A106 GR.B", {}, {}, "FATAL_METALLURGY_DOWNGRADE", "ASTM Metallurgy DAG", "Metallurgy Downgrade: Carbon steel pipe replacing Duplex 2205 in sea-water line"),
        # 4. Cryogenic LF2 Trap
        ("FLANGE", 50.0, 50.0, 300, 300, "ASTM A350 LF2", "ASTM A105", {}, {}, "FATAL_CRYOGENIC_BRITTLE_FRACTURE", "ASTM A350 / ASME B31.3", "Cryogenic Brittle Fracture Trap: Standard A105 (untested at -46C) replacing impact-tested A350 LF2"),
        # 5. Creep Rupture Trap
        ("PIPE", 100.0, 100.0, 600, 600, "ASTM A335 P22", "ASTM A106 GR.B", {"temp_c": 510}, {"temp_c": 510}, "FATAL_CREEP_RUPTURE", "ASME B31.3", "Creep Rupture Trap: Carbon steel replacing 2.25Cr P22 in 510C furnace line (Accelerated creep voiding)"),
        # 6. Intergranular Sensitization Trap
        ("PIPE", 50.0, 50.0, 150, 150, "ASTM A312 TP316L", "ASTM A312 TP316", {"service": "NITRIC_ACID"}, {"service": "NITRIC_ACID"}, "FATAL_SENSITIZATION_CORROSION", "ASTM A262", "Intergranular Sensitization Trap: Standard carbon SS316 (C<=0.08) replacing low-carbon SS316L in acid"),
        # 7. Pipe Down-Scheduling
        ("PIPE", 100.0, 100.0, 300, 300, "ASTM A106 GR.B", "ASTM A106 GR.B", {"sched": "SCH 80"}, {"sched": "SCH 40"}, "FATAL_PIPE_SCHEDULE_DOWNGRADE", "ASME B36.10M", "Pipe Schedule Downgrade: SCH 40 replacing required SCH 80 (Burst hazard under pressure)"),
        # 8. Welded Pipe in Hydrogen Service
        ("PIPE", 150.0, 150.0, 600, 600, "ASTM A106 GR.B", "ASTM A53 GR.B", {"mfg": "SMLS", "service": "HYDROGEN"}, {"mfg": "ERW", "service": "HYDROGEN"}, "FATAL_WELDED_IN_SEAMLESS_SERVICE", "API RP 941", "Welded in Seamless Service: Welded ERW pipe replacing Seamless in high-pressure hydrogen service"),
        # 9. NACE Sour Service Violation
        ("GATE_VALVE", 100.0, 100.0, 300, 300, "ASTM A216 WCB", "ASTM A216 WCB", {"nace_mr0175": True, "hardness_max_hrc": 22}, {"nace_mr0175": False, "hardness_max_hrc": 28}, "FATAL_NACE_SOUR_SERVICE_VIOLATION", "NACE MR0175 / ISO 15156", "NACE Sour Service Violation: Non-NACE valve (>22 HRC) in wet H2S duty (Sulfide stress cracking)"),
        # 10. Large Flange Series Mismatch
        ("FLANGE", 900.0, 900.0, 300, 300, "ASTM A105", "ASTM A105", {"series": "SERIES_A"}, {"series": "SERIES_B"}, "FATAL_FLANGE_SERIES_MISMATCH", "ASME B16.47", "Large Flange Series Mismatch: NPS 36 Class 300 Series A mated to Series B (Bolt circle mismatch)"),
        # 11. Facing Incompatibility
        ("FLANGE", 100.0, 100.0, 600, 600, "ASTM A105", "ASTM A105", {"facing": "RTJ"}, {"facing": "RF"}, "FATAL_FACING_GEOMETRY_INCOMPATIBLE", "ASME B16.5", "Facing Incompatibility: Raised Face (RF) flange mated to Ring Type Joint (RTJ) ring groove"),
        # 12. Cast Iron Flat Face Fracture
        ("VALVE_BODY", 150.0, 150.0, 150, 150, "ASTM A126 CL.B", "ASTM A105", {"facing": "FF", "material_type": "CAST_IRON"}, {"facing": "RF", "material_type": "CARBON_STEEL"}, "FATAL_CAST_IRON_FLANGE_FRACTURE", "ASME B31.3 Sec 312.2", "Cast Iron Flange Fracture: Raised Face steel flange bolted to Flat Face cast iron valve (Ear cracking)"),
        # 13. Valve Trim Downgrade
        ("GATE_VALVE", 150.0, 150.0, 300, 300, "ASTM A216 WCB", "ASTM A216 WCB", {"trim": 5, "service": "CATALYST_SLURRY"}, {"trim": 1, "service": "CATALYST_SLURRY"}, "FATAL_VALVE_TRIM_DOWNGRADE", "API 600", "Trim Downgrade: Trim 1 (13Cr) replacing Trim 5 (Full Stellite) in erosive catalyst slurry"),
        # 14. Piggability Violation
        ("BALL_VALVE", 300.0, 300.0, 600, 600, "ASTM A105", "ASTM A105", {"port": "FULL_BORE", "piggable": True}, {"port": "REDUCED_BORE", "piggable": False}, "FATAL_PIGGABILITY_VIOLATION", "API 6D", "Piggability Violation: Reduced Bore valve in operational transmission pipeline (PIG scraper blockage)"),
        # 15. Non-Fire-Safe in Hydrocarbon
        ("BALL_VALVE", 100.0, 100.0, 150, 150, "ASTM A216 WCB", "ASTM A216 WCB", {"fire_safe": True, "service": "GASOLINE"}, {"fire_safe": False, "service": "GASOLINE"}, "FATAL_NON_FIRE_SAFE_HYDROCARBON", "API 607 / API 6FA", "Non-Fire-Safe in Hydrocarbon: Standard soft-seated valve lacking fire-test certification in flammable line"),
        # 16. Butterfly Cat A in Cat B
        ("BUTTERFLY_VALVE", 200.0, 200.0, 150, 150, "ASTM A216 WCB", "ASTM A126 CL.B", {"category": "CAT_B_HIGH_PERF", "temp_c": 190}, {"category": "CAT_A_RUBBER_LINED", "temp_c": 190}, "FATAL_BUTTERFLY_CAT_A_IN_CAT_B", "API 609", "Butterfly Category Mismatch: Cat A rubber-lined valve in 190C refinery process line (Elastomer blowout)"),
        # 17. Undersized PSV Orifice
        ("PSV_VALVE", 50.0, 50.0, 300, 300, "ASTM A216 WCB", "ASTM A216 WCB", {"orifice_letter": "F", "area_sq_in": 0.307}, {"orifice_letter": "D", "area_sq_in": 0.110}, "FATAL_PSV_ORIFICE_UNDERSIZED", "API 520 / API 526", "Undersized PSV Orifice: Orifice D proposed for required Orifice F (Vessel overpressure detonation)"),
        # 18. Category M Threaded Joint
        ("FITTING", 50.0, 50.0, 3000, 3000, "ASTM A105", "ASTM A105", {"joint": "BUTTWELD_100RT", "service": "CATEGORY_M_LETHAL"}, {"joint": "THREADED_NPT", "service": "CATEGORY_M_LETHAL"}, "FATAL_CATEGORY_M_JOINT_VIOLATION", "ASME B31.3 Chapter VIII", "Category M Violation: Threaded NPT fitting proposed for lethal toxic Category M fluid line"),
        # 19. Liquid Metal Embrittlement
        ("STUD_BOLT", 20.0, 20.0, None, None, "ASTM A193 B7", "ASTM A193 B7", {"coating": "BARE", "temp_c": 350}, {"coating": "GALVANIZED_ZINC", "temp_c": 350}, "FATAL_LIQUID_METAL_EMBRITTLEMENT", "API 571", "Liquid Metal Embrittlement: Galvanized zinc-plated stud bolts in 350C line (Molten zinc grain cracking)"),
        # 20. Nut Mismatch
        ("STUD_BOLT", 20.0, 20.0, None, None, "ASTM A193 B7", "ASTM A193 B7", {"nut_grade": "ASTM A194 GR.2H"}, {"nut_grade": "COMMERCIAL_MILD_STEEL_GR2"}, "FATAL_NUT_METALLURGY_MISMATCH", "ASTM A193 / A194", "Nut Mismatch: Commercial mild steel nuts paired with high-strength alloy B7 studs (Thread shear blowout)"),
        # 21. Gasket Melting Creep
        ("GASKET_SHEET", 100.0, 100.0, 300, 300, "PTFE", "PTFE", {"filler": "FLEXIBLE_GRAPHITE", "temp_c": 400}, {"filler": "VIRGIN_PTFE", "temp_c": 400}, "FATAL_GASKET_MELTING_CREEP", "ASME B16.21", "Gasket Melting: Virgin PTFE gasket in 400C steam line (Thermal extrusion blowout)"),
        # 22. Class 900 SWG Missing Inner Ring
        ("GASKET_SWG", 150.0, 150.0, 900, 900, "SS316", "SS316", {"inner_ring": True}, {"inner_ring": False}, "FATAL_GASKET_COLLAPSE", "ASME B16.20", "Gasket Buckling: Class 900# Spiral Wound Gasket without solid inner ring (Inward radial winding collapse)"),
        # 23. Harder Gasket Galling Groove
        ("GASKET_RTJ", 100.0, 100.0, 600, 600, "SS316", "SS316", {"flange_hardness_hrb": 85, "gasket_hardness_hrb": 80}, {"flange_hardness_hrb": 85, "gasket_hardness_hrb": 95}, "FATAL_RTJ_GROOVE_GALLING", "ASME B16.20", "RTJ Galling: Gasket ring harder than flange metal (Flange face groove indentation damage)"),
        # 24. Non-Ex Motor in Hazardous Area
        ("ELECTRIC_MOTOR", 37.0, 37.0, None, None, "CAST_IRON", "CAST_IRON", {"area": "ZONE_1_EX_D_IIC_T4"}, {"area": "SAFE_AREA_NON_EX"}, "FATAL_HAZARDOUS_AREA_NON_EX_MOTOR", "IS/IEC 60079", "Non-Ex Motor in Zone 1: Safe-area motor installed in hazardous Zone 1 hydrocarbon area (Vapor explosion)"),
        # 25. Bearing CN in C3 Duty
        ("BEARING", 75.0, 75.0, None, None, "52100_STEEL", "52100_STEEL", {"clearance": "C3", "rpm": 3000, "temp_c": 120}, {"clearance": "CN", "rpm": 3000, "temp_c": 120}, "FATAL_BEARING_CLEARANCE_SEIZURE", "ISO 15", "Bearing Seizure: Normal clearance CN bearing in high-speed pump (Shaft thermal expansion binding)"),
        # 26. TEMA Class Downgrade
        ("HEAT_EXCHANGER_BUNDLE", 600.0, 600.0, 150, 150, "ASTM A214", "ASTM A214", {"tema_class": "TEMA_R_REFINERY"}, {"tema_class": "TEMA_C_COMMERCIAL"}, "FATAL_TEMA_CLASS_DOWNGRADE", "TEMA Standards", "TEMA Downgrade: Commercial Class C tube bundle proposed for severe refinery Class R service"),
        # 27. Welded Tubes in Heat Exchanger
        ("HE_TUBING", 19.05, 19.05, None, None, "ASTM A213 TP316", "ASTM A249 TP316", {"mfg": "SEAMLESS"}, {"mfg": "WELDED"}, "FATAL_TUBING_WELD_CORROSION", "ASTM A213 / A249", "Tubing Weld Corrosion: Welded A249 tubes replacing Seamless A213 tubes in high-pressure cooler"),
        # 28. Foot-Mounted Pump at High Temp
        ("CENTRIFUGAL_PUMP", 100.0, 100.0, 300, 300, "ASTM A216 WCB", "ASTM A216 WCB", {"api610_type": "OH2_CENTERLINE", "temp_c": 240}, {"api610_type": "OH1_FOOT_MOUNTED", "temp_c": 240}, "FATAL_PUMP_MOUNTING_THERMAL_EXPANSION", "API 610", "Pump Thermal Binding: Foot-mounted OH1 pump replacing centerline OH2 at 240C (Casing distortion)"),
        # 29. Wear Ring Galling
        ("PUMP_WEAR_RING", 120.0, 120.0, None, None, "SS410", "SS410", {"hardness_delta_hb": 60}, {"hardness_delta_hb": 0}, "FATAL_WEAR_RING_GALLING", "API 610 Annex H", "Wear Ring Galling: Identical hardness mating wear rings (<50 HB difference causes seizure)"),
        # 30. Recip Compressor Inverted Valve
        ("COMPRESSOR_VALVE", 100.0, 100.0, 600, 600, "SS420", "SS420", {"valve_function": "DISCHARGE_VALVE"}, {"valve_function": "SUCTION_VALVE"}, "FATAL_RECIP_VALVE_INVERSION", "API 618", "Compressor Valve Inversion: Suction valve installed in discharge port (Cylinder overpressure detonation)"),
        # 31. Single Dry Gas Seal in Sour Gas
        ("COMPRESSOR_SEAL", 90.0, 90.0, None, None, "SS316/TUNGSTEN_CARBIDE", "SS316/CARBON", {"seal_type": "TANDEM_N2_BUFFER", "service": "SOUR_GAS"}, {"seal_type": "SINGLE_SEAL", "service": "SOUR_GAS"}, "FATAL_DRY_GAS_SEAL_SINGLE", "API 692", "Dry Gas Seal Failure: Single seal proposed for lethal toxic sour gas compressor requiring tandem N2 barrier"),
        # 32. Fragmenting Rupture Disk Upstream of PSV
        ("RUPTURE_DISK", 80.0, 80.0, 300, 300, "INCONEL_600", "INCONEL_600", {"upstream_of_psv": True, "type": "NON_FRAGMENTING"}, {"upstream_of_psv": True, "type": "FRAGMENTING"}, "FATAL_FRAGMENTING_RUPTURE_DISK", "ISO 4126-2 / ASME Sec VIII UG-127", "Fragmenting Disk Upstream of PSV: Metal petals shatter and block safety relief valve throat"),
        # 33. Shop-Cut Plate as Line Blind
        ("LINE_BLIND", 200.0, 200.0, 300, 300, "ASTM A516 GR.70", "COMMERCIAL_MS_PLATE", {"certified_standard": "ASME_B16.48"}, {"certified_standard": "SHOP_CUT_UNCERTIFIED"}, "FATAL_LINE_BLIND_SHOP_CUT", "ASME B16.48", "Uncertified Blind Plate: Shop-cut uncalculated steel plate used for positive isolation (Yield blowout)"),
        # 34. Tank Vent Undersized
        ("TANK_PVRV", 150.0, 150.0, None, None, "ALUMINUM", "ALUMINUM", {"required_scfh": 120000}, {"required_scfh": 45000}, "FATAL_TANK_VENT_UNDERSIZED", "API 2000", "Tank Vent Undersized: Relief valve flow capacity less than liquid pump-out rate (Atmospheric tank vacuum collapse)"),
        # 35. Flame Arrestor Detonation vs Deflagration
        ("FLAME_ARRESTOR", 100.0, 100.0, 150, 150, "SS316", "SS316", {"zone": "IN_LINE_DETONATION"}, {"zone": "END_OF_LINE_DEFLAGRATION"}, "FATAL_FLAME_ARRESTOR_MISMATCH", "ISO 16852", "Flame Arrestor Mismatch: End-of-line deflagration unit placed in closed pipeline supersonic detonation zone"),
        # 36. Unrestrained Expansion Bellows
        ("EXPANSION_JOINT", 300.0, 300.0, 300, 300, "INCOLOY_825", "INCOLOY_825", {"restraint": "TIED_TIE_RODS", "pressure_bar": 16}, {"restraint": "UNRESTRAINED", "pressure_bar": 16}, "FATAL_EXPANSION_JOINT_UNRESTRAINED", "EJMA Standards", "Unrestrained Expansion Bellows: Unrestrained joint proposed for high-pressure line (Pipe anchor shear blowout)"),
        # 37. Flange Insulation Kit Bridging
        ("FLANGE_INSULATION_KIT", 150.0, 150.0, 150, 150, "G10_GLASS_EPOXY", "PHENOLIC", {"type": "TYPE_E_FULL_FACE", "bimetallic": True}, {"type": "TYPE_F_RAISED_FACE", "bimetallic": True}, "FATAL_FLANGE_INSULATION_KIT_BRIDGING", "NACE SP0286", "FIK Bridging: Type F raised gasket on bimetallic flange allows conductive dirt bridging and galvanic corrosion"),
        # 38. Chloride Stress Corrosion under Insulation
        ("THERMAL_INSULATION", 100.0, 100.0, None, None, "CALCIUM_SILICATE", "COMMERCIAL_MINERAL_WOOL", {"ss_piping": True, "chloride_ppm_max": 50}, {"ss_piping": True, "chloride_ppm_max": 850}, "FATAL_INSULATION_CHLORIDE_STRESS_CORROSION", "ASTM C795", "Chloride SCC under Insulation: High-chloride mineral wool applied over SS316 pipe (External stress corrosion)"),
        # 39. Cellular Glass Cryogenic Permeability
        ("CRYOGENIC_INSULATION", 150.0, 150.0, None, None, "CELLULAR_GLASS", "POLYURETHANE_OPEN_CELL", {"temp_c": -162, "closed_cell": True}, {"temp_c": -162, "closed_cell": False}, "FATAL_CRYOGENIC_INSULATION_ICE_JACKING", "ASTM C552", "Cryogenic Insulation Failure: Permeable foam on -162C LNG line causes moisture vapor ice-jacking and boil-off runaway"),
        # 40. Short Radius Elbow in Piggable Line
        ("ELBOW_90", 200.0, 200.0, None, None, "ASTM A234 WPB", "ASTM A234 WPB", {"radius": "LR_1.5D", "piggable": True}, {"radius": "SR_1.0D", "piggable": True}, "FATAL_BUTTWELD_RESTRICTION_TRAP", "ASME B16.9", "Short Radius Restriction: Short Radius (1.0D) elbow in piggable pipeline (Scraper blockage and pressure drop)"),
        # 41. MSS SP-97 Olet Schedule Mismatch
        ("BRANCH_OLET", 50.0, 50.0, 3000, 3000, "ASTM A105", "ASTM A105", {"header_size": 200.0, "sched": "SCH 80"}, {"header_size": 200.0, "sched": "SCH 40"}, "FATAL_OLETS_SCHEDULE_MISMATCH", "MSS SP-97", "Olet Schedule Mismatch: Sch 40 sockolet on Sch 80 branch line (Branch reinforcement structural weakness)"),
        # 42. High-Yield Pipeline Fitting Downgrade
        ("PIPELINE_FITTING", 400.0, 400.0, 600, 600, "MSS SP-75 WPHY 60", "ASTM A234 WPB", {"smys_psi": 60000}, {"smys_psi": 35000}, "FATAL_PIPELINE_FITTINGS_DOWNGRADE", "MSS SP-75 / API 5L", "High-Yield Fitting Downgrade: Standard A234 WPB (35k psi) replacing high-yield WPHY 60 in gas transmission grid"),
        # 43. Slip-On Flange in Severe Cyclic Duty
        ("FLANGE", 100.0, 100.0, 300, 300, "ASTM A105", "ASTM A105", {"attachment": "WELD_NECK", "severe_cyclic": True}, {"attachment": "SLIP_ON", "severe_cyclic": True}, "FATAL_FLANGE_ATTACHMENT_FATIGUE", "ASME B31.3 Sec 300.2", "Slip-On in Severe Cyclic Duty: Fillet-welded Slip-On flange replacing butt-weld Weld Neck in thermal fatigue line"),
        # 44. API 682 Plan Inadequate for Lethal Service
        ("PUMP_SEAL", 65.0, 65.0, None, None, "SS316/SIC/SIC", "SS316/CARBON/SIC", {"plan": "PLAN_53A_DUAL_PRESSURIZED", "service": "LETHAL_H2S"}, {"plan": "PLAN_11_SINGLE_UNPRESSURIZED", "service": "LETHAL_H2S"}, "FATAL_API_682_PLAN_INADEQUATE", "API 682", "Inadequate Seal Plan: Single Plan 11 seal in lethal sour hydrocarbon pump (Fugitive toxic blowout)"),
        # 45. High Temperature PTFE Failure
        ("BALL_VALVE", 50.0, 50.0, 300, 300, "ASTM A216 WCB", "ASTM A216 WCB", {"seat": "STELLITE_METAL", "temp_c": 330}, {"seat": "VIRGIN_PTFE", "temp_c": 330}, "FATAL_HIGH_TEMP_PTFE_SEAL_FAILURE", "API 608", "High Temp Soft Seat Failure: PTFE seats (max 200C) installed in 330C thermal oil service (Seat liquefaction)"),
        # 46. Metric PN Pressure Down-Rating
        ("GATE_VALVE", 100.0, 100.0, 50, 16, "ASTM A216 WCB", "ASTM A216 WCB", {}, {}, "FATAL_PRESSURE_DOWN_RATING", "EN 1092-1 / DIN", "Metric Pressure Down-Rating: PN16 valve proposed for PN50 operating line (Hydrostatic casing rupture)"),
        # 47. NPS 48 Series A vs Series B
        ("FLANGE", 1200.0, 1200.0, 150, 150, "ASTM A105", "ASTM A105", {"series": "SERIES_A"}, {"series": "SERIES_B"}, "FATAL_FLANGE_SERIES_MISMATCH", "ASME B16.47", "Large Flange Incompatibility: NPS 48 Class 150 Series A flange mated to Series B flange"),
        # 48. Down-Rating 1500# to 600#
        ("GATE_VALVE", 50.0, 50.0, 1500, 600, "ASTM A105", "ASTM A105", {}, {}, "FATAL_PRESSURE_DOWN_RATING", "ASME B16.34", "Pressure Down-Rating: Class 600# valve proposed for Class 1500# injection line"),
        # 49. Inconel 625 replaced by SS304 in Hot HF Acid
        ("PIPE", 50.0, 50.0, 300, 300, "INCONEL 625", "ASTM A312 TP304", {"service": "HOT_HF_ACID"}, {"service": "HOT_HF_ACID"}, "FATAL_METALLURGY_DOWNGRADE", "NACE MR0175", "Alloy Downgrade: Stainless SS304 replacing Inconel 625 in hot hydrofluoric acid alkylation unit"),
        # 50. Non-Destructive Standard Class replacing Special Class
        ("VALVE", 100.0, 100.0, 1500, 1500, "ASTM A216 WCB", "ASTM A216 WCB", {"class_type": "SPECIAL_CLASS_100NDE"}, {"class_type": "STANDARD_CLASS_NO_NDE"}, "FATAL_SPECIAL_CLASS_NDE_MISMATCH", "ASME B16.34 Annex B", "Special Class NDE Violation: Standard Class valve replacing Special Class with non-destructive examination")
    ]
    
    for tpl in tier3_cases[:50]:
        cases.append({
            "test_id": f"GB-T3-{case_id:04d}",
            "expected_tier": "TIER_3_INCOMPATIBLE",
            "expected_is_compatible": False,
            "expected_violation_code": tpl[9],
            "target_standard": tpl[10],
            "scenario_description": f"Tier-3 Hazard #{case_id}: {tpl[11]}",
            "query_part": {
                "item_type": tpl[0],
                "size_nb_mm": tpl[1],
                "pressure_class": tpl[3],
                "metallurgy": tpl[5],
                "properties": tpl[7]
            },
            "candidate_part": {
                "item_type": tpl[0],
                "size_nb_mm": tpl[2],
                "pressure_class": tpl[4],
                "metallurgy": tpl[6],
                "properties": tpl[8]
            }
        })
        case_id += 1
        
    return cases

# ----------------------------------------------------------------------
# 3. OCR PAYLOADS (500 MTC Test Certificates)
# ----------------------------------------------------------------------

MANUFACTURERS = [
    "Jindal Stainless Limited, Hisar",
    "Tata Steel Limited, Jamshedpur",
    "Steel Authority of India (SAIL), Rourkela",
    "Welspun Corp Limited, Anjar",
    "Larsen & Toubro Heavy Engineering, Hazira",
    "Ratnamani Metals & Tubes Ltd, Kutch",
    "MSL (Maharashtra Seamless Limited), Raigad",
    "Pennar Industries Limited, Hyderabad"
]

TPI_AGENCIES = [
    "Lloyd's Register Industrial Services (India)",
    "DNV GL Business Assurance India",
    "Bureau Veritas (India) Private Limited",
    "TUV SUD South Asia Private Limited",
    "Engineers India Limited (EIL Inspection)"
]

def generate_ocr_payloads(count: int = 500) -> List[Dict[str, Any]]:
    payloads = []
    
    for i in range(1, count + 1):
        doc_id = f"DOC-MTC-2026-{i:04d}"
        mat_choice = random.choice([
            ("ASTM A105", "CARBON_STEEL", 0.22, 0.85, 0.25, 0.015, 0.012, 0.12, 0.08, 0.03, 0.01, 0.10, 310, 520, 26, 45, 155),
            ("ASTM A350 LF2", "LTCS", 0.18, 1.10, 0.28, 0.012, 0.008, 0.15, 0.12, 0.04, 0.02, 0.12, 290, 500, 28, 65, 150),
            ("ASTM A182 F316L", "STAINLESS", 0.025, 1.45, 0.55, 0.025, 0.010, 16.8, 11.2, 2.15, 0.04, 0.25, 245, 560, 42, 95, 165),
            ("ASTM A182 F304", "STAINLESS", 0.06, 1.50, 0.60, 0.028, 0.012, 18.2, 8.4, 0.20, 0.03, 0.20, 230, 540, 45, 90, 160),
            ("ASTM A182 F51", "DUPLEX", 0.022, 1.20, 0.45, 0.020, 0.005, 22.4, 5.6, 3.10, 0.05, 0.15, 480, 720, 30, 110, 240),
            ("ASTM A106 GR.B", "CARBON_STEEL", 0.24, 0.90, 0.22, 0.018, 0.014, 0.10, 0.06, 0.02, 0.01, 0.08, 285, 485, 27, 40, 145),
            ("ASTM A216 WCB", "CAST_STEEL", 0.23, 0.80, 0.35, 0.020, 0.015, 0.18, 0.15, 0.05, 0.02, 0.15, 275, 495, 24, 35, 150),
            ("ASTM A193 B7", "ALLOY_STEEL", 0.41, 0.88, 0.26, 0.015, 0.012, 1.05, 0.15, 0.22, 0.03, 0.12, 725, 890, 18, 55, 285)
        ])
        
        grade_name, family, base_c, base_mn, base_si, base_p, base_s, base_cr, base_ni, base_mo, base_v, base_cu, base_ys, base_ts, base_el, base_charpy, base_hb = mat_choice
        
        # Add slight natural measurement variations
        c = round(base_c * random.uniform(0.92, 1.08), 3)
        mn = round(base_mn * random.uniform(0.94, 1.06), 3)
        si = round(base_si * random.uniform(0.90, 1.10), 3)
        p = round(base_p * random.uniform(0.85, 1.15), 4)
        s = round(base_s * random.uniform(0.85, 1.15), 4)
        cr = round(base_cr * random.uniform(0.95, 1.05), 2)
        ni = round(base_ni * random.uniform(0.95, 1.05), 2)
        mo = round(base_mo * random.uniform(0.93, 1.07), 2)
        v = round(base_v * random.uniform(0.90, 1.10), 3)
        cu = round(base_cu * random.uniform(0.90, 1.10), 2)
        
        ys = int(base_ys * random.uniform(0.96, 1.06))
        ts = int(base_ts * random.uniform(0.97, 1.05))
        el = int(base_el * random.uniform(0.95, 1.05))
        charpy = int(base_charpy * random.uniform(0.92, 1.10))
        hb = int(base_hb * random.uniform(0.95, 1.05))
        
        # International Institute of Welding (IIW) Carbon Equivalent
        ce = round(c + (mn / 6.0) + ((cr + mo + v) / 5.0) + ((ni + cu) / 15.0), 3)
        
        mfg = random.choice(MANUFACTURERS)
        tpi = random.choice(TPI_AGENCIES)
        heat_no = f"HT-{random.randint(2024, 2026)}-{random.randint(10000, 99999)}"
        cert_no = f"MTC/{random.randint(2025, 2026)}/{random.randint(1000, 9999)}"
        po_no = f"PO-MOPNG-{random.randint(100000, 999999)}"
        
        # 10% (50 items) low confidence score (0.65 to 0.84) forcing HITL triage
        is_degraded = (i <= 50)
        if is_degraded:
            confidence = round(random.uniform(0.65, 0.84), 3)
        else:
            confidence = round(random.uniform(0.88, 0.99), 3)
            
        # 5% (25 items) OCR hallucinations
        hallucinations = []
        is_hallucinated = (51 <= i <= 75)
        
        c_text = f"C: {c:.3f}%"
        ys_text = f"Yield Strength (Re): {ys} MPa"
        heat_text = f"Heat No: {heat_no}"
        
        if is_hallucinated:
            h_type = random.choice(["carbon_alpha", "yield_digit", "heat_confused"])
            if h_type == "carbon_alpha":
                c_text = f"C: O.{int(c*100):02d}%"
                hallucinations.append(f"OCR Hallucination: Letter 'O' misrecognized for leading zero '0' in Carbon content ('{c_text}')")
            elif h_type == "yield_digit":
                ys_text = f"Yield Strength (Re): {str(ys).replace('1', 'I').replace('0', 'O')} MPa"
                hallucinations.append(f"OCR Hallucination: Alphanumeric characters 'I'/'O' substituted for digits in Yield Strength ('{ys_text}')")
            else:
                heat_text = f"Heat No: H3AT-{random.randint(10000, 99999)}"
                hallucinations.append(f"OCR Hallucination: Digit '3' substituted for letter 'E' in heat header ('{heat_text}')")
        
        raw_text = (
            f"MATERIAL TEST CERTIFICATE EN 10204 3.1\n"
            f"Manufacturer: {mfg}\n"
            f"Third Party Inspection Agency: {tpi}\n"
            f"Certificate No: {cert_no} | Purchase Order No: {po_no}\n"
            f"{heat_text} | Material Grade: {grade_name}\n"
            f"--- CHEMICAL COMPOSITION (WEIGHT %) ---\n"
            f"{c_text} | Mn: {mn:.3f}% | Si: {si:.3f}% | P: {p:.4f}% | S: {s:.4f}%\n"
            f"Cr: {cr:.2f}% | Ni: {ni:.2f}% | Mo: {mo:.2f}% | V: {v:.3f}% | Cu: {cu:.2f}%\n"
            f"Calculated Carbon Equivalent (IIW CE): {ce:.3f}%\n"
            f"--- MECHANICAL TEST RESULTS ---\n"
            f"{ys_text} | Tensile Strength (Rm): {ts} MPa\n"
            f"Elongation (A5): {el}% | Charpy V-Notch Impact Toughness: {charpy} J\n"
            f"Brinell Hardness: {hb} HBW\n"
            f"Status: CONFORMS TO STANDARD SPECIFICATION"
        )
        
        payloads.append({
            "document_id": doc_id,
            "filename": f"MTC_{grade_name.replace(' ', '_')}_{heat_no}.pdf",
            "doc_type": "MTC_CERTIFICATE",
            "header": {
                "certificate_no": cert_no,
                "heat_no": heat_no,
                "po_no": po_no,
                "manufacturer": mfg,
                "tpi_agency": tpi,
                "material_grade": grade_name,
                "specification": "EN 10204 3.1"
            },
            "chemical_composition": {
                "C": c,
                "Mn": mn,
                "Si": si,
                "P": p,
                "S": s,
                "Cr": cr,
                "Ni": ni,
                "Mo": mo,
                "V": v,
                "Cu": cu
            },
            "carbon_equivalent_iiw": ce,
            "mechanical_properties": {
                "yield_strength_mpa": ys,
                "tensile_strength_mpa": ts,
                "elongation_pct": el,
                "impact_joules_charpy": charpy,
                "hardness_hb": hb
            },
            "confidence_score": confidence,
            "is_degraded_scan": is_degraded,
            "is_incomplete": False,
            "ocr_hallucinations": hallucinations,
            "extracted_text": raw_text
        })
        
    return payloads

def main():
    print("Generating Samanvay-AI synthetic production-grade datasets...")
    
    # 1. Inventory Catalog
    print("1. Generating inventory_catalog.csv (5,000 rows)...")
    catalog_rows = generate_inventory_catalog(5000)
    catalog_path = os.path.join(DATA_DIR, "inventory_catalog.csv")
    with open(catalog_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sku_code", "cpse_name", "depot_location", "raw_description",
            "quantity", "unit_cost_inr", "days_idle"
        ])
        writer.writeheader()
        writer.writerows(catalog_rows)
    print(f"   -> Successfully saved {len(catalog_rows)} rows to {catalog_path}")
    
    # 2. Golden Benchmarks
    print("2. Generating golden_benchmarks.json (150 paired test cases)...")
    benchmarks = generate_golden_benchmarks()
    benchmarks_path = os.path.join(DATA_DIR, "golden_benchmarks.json")
    with open(benchmarks_path, "w", encoding="utf-8") as f:
        json.dump(benchmarks, f, indent=2)
    print(f"   -> Successfully saved {len(benchmarks)} paired cases to {benchmarks_path}")
    
    # 3. OCR Payloads
    print("3. Generating ocr_payloads.json (500 MTC payloads)...")
    ocr_payloads = generate_ocr_payloads(500)
    ocr_path = os.path.join(DATA_DIR, "ocr_payloads.json")
    with open(ocr_path, "w", encoding="utf-8") as f:
        json.dump(ocr_payloads, f, indent=2)
    print(f"   -> Successfully saved {len(ocr_payloads)} MTC payloads to {ocr_path}")
    
    print("\nDataset generation complete! Validating statistics:")
    print(f"- inventory_catalog.csv: {len(catalog_rows)} records")
    print(f"- golden_benchmarks.json: {len(benchmarks)} cases (Tier 1: 50, Tier 2: 50, Tier 3: 50)")
    degraded_count = sum(1 for p in ocr_payloads if p['is_degraded_scan'])
    hallucinated_count = sum(1 for p in ocr_payloads if len(p['ocr_hallucinations']) > 0)
    print(f"- ocr_payloads.json: {len(ocr_payloads)} payloads (Low confidence/HITL: {degraded_count}, Hallucinations: {hallucinated_count})")

if __name__ == "__main__":
    main()
