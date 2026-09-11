"""
build_train_sets.py
Constructs annotated datasets for Machine Learning pipelines:
1. Token Classification (NER): 5,000 samples with character-level offsets.
2. Bi-Encoder Contrastive Pairs: 8,000 paired samples for MultipleNegativesRankingLoss (MNRL).
Author: Data Pipelines & Taxonomy Lead (Shaurya)
"""

import os
import csv
import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
TAXONOMY_DIR = DATA_DIR / "taxonomies"
ML_DIR = DATA_DIR / "ml_training"
ML_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)

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

# -----------------------------------------------------------------------------
# TASK 1: NER Dataset Generator (5,000 samples)
# -----------------------------------------------------------------------------

ITEM_TYPE_VARIANTS = {
    "FLANGE_WELD_NECK": ["FLG WN", "FLANGE WELD NECK", "FLANGE, WELDING NECK", "FLG-WN", "WELD NECK FLANGE", "FLG"],
    "FLANGE_BLIND": ["FLG BLD", "BLIND FLANGE", "FLANGE, BLIND", "FLG-BLD", "BLD FLG"],
    "FLANGE_SLIP_ON": ["FLG SO", "SLIP ON FLANGE", "FLANGE, SLIP-ON", "FLG-SO", "SO FLG"],
    "GATE_VALVE": ["VLV GT", "GATE VALVE", "VALVE, GATE", "VLV-GT", "GT VLV", "VALVE GATE"],
    "BALL_VALVE": ["VLV BL", "BALL VALVE", "VALVE, BALL", "VLV-BL", "BL VLV"],
    "GLOBE_VALVE": ["VLV GLB", "GLOBE VALVE", "VALVE, GLOBE", "VLV-GL", "GLB VLV"],
    "SPIRAL_WOUND_GASKET": ["GSKT SPWD", "SPIRAL WOUND GASKET", "GASKET, SPIRAL WOUND", "GSKT-SW", "SPWD GSKT"],
    "STUD_BOLT": ["STUDBLT", "STUD BOLT", "STUD BOLT WITH NUTS", "BLT-STUD", "STUD BOLTS"]
}

FACING_VARIANTS = {
    "RF": ["RF", "RAISED FACE", "RF FACING", "WNRF"],
    "RTJ": ["RTJ", "RING TYPE JOINT", "RTJ FACING"],
    "FF": ["FF", "FLAT FACE", "FF FACING"],
    "BW": ["BW", "BUTT WELD", "BW ENDS"],
    "SW": ["SW", "SOCKET WELD", "SW ENDS"],
    "THRD": ["THRD", "THREADED", "NPT THREADED"]
}

PRESSURE_VARIANTS = {
    150: ["150#", "150LB", "CLASS 150", "CL150", "PN20", "150 LBS", "CL-150"],
    300: ["300#", "300LB", "CLASS 300", "CL300", "PN50", "300 LBS", "CL-300"],
    600: ["600#", "600LB", "CLASS 600", "CL600", "PN100", "600 LBS", "CL-600"],
    900: ["900#", "900LB", "CLASS 900", "CL900", "PN150", "900 LBS", "CL-900"],
    1500: ["1500#", "1500LB", "CLASS 1500", "CL1500", "PN250", "1500 LBS", "CL-1500"]
}

METALLURGY_VARIANTS = {
    "ASTM A105": ["A105", "ASTM A105", "ASTM A105N", "CS A105", "CARBON STEEL A105"],
    "ASTM A350 LF2": ["A350-LF2", "A350LF2", "ASTM A350 LF2", "LF2", "LTCS A350 LF2"],
    "ASTM A182 F304": ["SS304", "ASTM A182 F304", "F304", "AISI 304", "SS-304"],
    "ASTM A182 F316": ["SS316", "ASTM A182 F316", "F316", "AISI 316", "SS-316", "SS316L"],
    "ASTM A216 WCB": ["WCB", "ASTM A216 WCB", "A216-WCB", "CAST STEEL WCB"],
    "SS316 / GRAPHITE": ["SS316/GRAF", "SS316-GR", "SS316 / GRAPHITE", "316SS/GRAPHITE"],
    "SS304 / GRAPHITE": ["SS304/GRAF", "SS304-GR", "SS304 / GRAPHITE"],
    "ASTM A193 B7 / A194 2H": ["B7/2H", "B7-2H", "ASTM A193 B7", "GR B7 / 2H"],
    "ASTM A320 L7 / A194 7": ["L7/GR7", "L7-GR7", "ASTM A320 L7", "GR L7 / 7"]
}

def generate_size_variant(nb_mm, inch_str, dn_code):
    options = [
        inch_str.replace('"', 'IN'),
        inch_str,
        inch_str.replace('"', ' INCH'),
        dn_code,
        f"{int(float(nb_mm))}MM",
        f"{int(float(nb_mm))} MM",
        f"DN {int(float(nb_mm))}"
    ]
    return random.choice(options)

def assemble_annotated_sample(item):
    """
    Constructs a noised sample string and tracks precise character offsets.
    """
    item_type = item["item_type"]
    size_mm = item["size_nb_mm"]
    size_inch = item["size_inch"]
    dn_code = item["dn_code"]
    p_class = int(item["pressure_class"])
    mat = item["metallurgy"]
    facing = item["facing_end"]
    std = item["standard"]
    
    # Select token variants
    t_val = random.choice(ITEM_TYPE_VARIANTS.get(item_type, [item_type]))
    s_val = generate_size_variant(size_mm, size_inch, dn_code)
    p_val = random.choice(PRESSURE_VARIANTS.get(p_class, [f"{p_class}#"]))
    m_val = random.choice(METALLURGY_VARIANTS.get(mat, [mat]))
    f_val = random.choice(FACING_VARIANTS.get(facing, [facing]))
    
    std_variants = [std, std.replace(" ", ""), std.replace("ASME ", "ANSI/ASME ")]
    std_val = random.choice(std_variants) if random.random() < 0.65 else None
    
    # Random token ordering templates
    style = random.choice(["standard", "scrambled", "hyphenated", "comma_delimited"])
    
    tokens = []
    if style == "hyphenated":
        elements = [("ITEM_TYPE", t_val), ("SIZE", s_val), ("PRESSURE_RATING", p_val), ("METALLURGY", m_val), ("FACING_END", f_val)]
        if std_val:
            elements.append(("STANDARD", std_val))
        delim = "-"
    elif style == "comma_delimited":
        elements = [("ITEM_TYPE", t_val), ("SIZE", s_val), ("PRESSURE_RATING", p_val), ("METALLURGY", m_val), ("FACING_END", f_val)]
        if std_val:
            elements.append(("STANDARD", std_val))
        delim = ", "
    elif style == "scrambled":
        elements = [("ITEM_TYPE", t_val), ("FACING_END", f_val), ("SIZE", s_val), ("PRESSURE_RATING", p_val), ("METALLURGY", m_val)]
        if std_val:
            elements.append(("STANDARD", std_val))
        delim = " "
    else: # standard space delimited
        elements = [("ITEM_TYPE", t_val), ("SIZE", s_val), ("PRESSURE_RATING", p_val), ("METALLURGY", m_val), ("FACING_END", f_val)]
        if std_val:
            elements.append(("STANDARD", std_val))
        delim = " "
        
    full_text = ""
    labels = []
    
    for idx, (label, val) in enumerate(elements):
        start = len(full_text)
        full_text += val
        end = len(full_text)
        labels.append({"start": start, "end": end, "label": label})
        if idx < len(elements) - 1:
            full_text += delim
            
    # Verify offset integrity
    for lbl in labels:
        assert full_text[lbl["start"]:lbl["end"]] != "", "Empty offset slice!"
        
    return {"text": full_text, "labels": labels}

def build_ner_dataset(canonical_items, target_count=5000):
    print(f"Generating {target_count} NER samples...")
    ner_file = ML_DIR / "ner_train.jsonl"
    
    samples = []
    sampled = random.choices(canonical_items, k=target_count)
    for item in sampled:
        samples.append(assemble_annotated_sample(item))
        
    with open(ner_file, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
            
    print(f"[+] Wrote {len(samples)} NER records to {ner_file.name}")

# -----------------------------------------------------------------------------
# TASK 2: Bi-Encoder Contrastive Dataset (8,000 pairs)
# -----------------------------------------------------------------------------

def build_biencoder_dataset(canonical_items, target_count=8000):
    print(f"Generating {target_count} Bi-Encoder contrastive pairs...")
    biencoder_file = ML_DIR / "biencoder_pairs.jsonl"
    
    pairs = []
    sampled = random.choices(canonical_items, k=target_count)
    
    for item in sampled:
        # Generate an informal/messy CPSE-style query string
        cpse_tag = random.choice(["IOCL", "ONGC", "BPCL", "REQUISITION", "INQUIRY"])
        
        sample_ner = assemble_annotated_sample(item)
        messy_str = f"{cpse_tag}: {sample_ner['text']}"
        
        # Standard positive canonical description
        positive_str = f"CANONICAL: {item['canonical_description']}"
        
        pairs.append({
            "anchor": messy_str,
            "positive": positive_str,
            "canonical_id": item["canonical_id"],
            "item_type": item["item_type"],
            "size_nb_mm": float(item["size_nb_mm"]),
            "pressure_class": int(item["pressure_class"])
        })
        
    with open(biencoder_file, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
            
    print(f"[+] Wrote {len(pairs)} contrastive pairs to {biencoder_file.name}")

def main():
    canonical_items = load_canonical_master()
    build_ner_dataset(canonical_items, target_count=5000)
    build_biencoder_dataset(canonical_items, target_count=8000)

if __name__ == "__main__":
    main()
