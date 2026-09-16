import csv
from pathlib import Path

# 1. Append pipes to canonical_master.csv
canonical_path = Path("data/taxonomies/canonical_master.csv")
new_canonicals = [
    {
        "canonical_id": "CAN-0006201",
        "item_type": "PIPE_SEAMLESS",
        "size_nb_mm": 50.0,
        "size_inch": '2"',
        "dn_code": "DN50",
        "pressure_class": 0,
        "metallurgy": "ASTM A106 GR.B",
        "facing_end": "BW",
        "standard": "ASME B36.10M",
        "canonical_description": 'PIPE, SEAMLESS, 2" (DN50), SCH 40, ASTM A106 GR.B, BEVELED ENDS, ASME B36.10M',
        "unspsc_code": "40171502",
        "gem_category_id": "GEM-PIPE-SEAMLESS",
    },
    {
        "canonical_id": "CAN-0006202",
        "item_type": "PIPE_SEAMLESS",
        "size_nb_mm": 100.0,
        "size_inch": '4"',
        "dn_code": "DN100",
        "pressure_class": 0,
        "metallurgy": "ASTM A106 GR.B",
        "facing_end": "BW",
        "standard": "ASME B36.10M",
        "canonical_description": 'PIPE, SEAMLESS, 4" (DN100), SCH 40, ASTM A106 GR.B, BEVELED ENDS, ASME B36.10M',
        "unspsc_code": "40171502",
        "gem_category_id": "GEM-PIPE-SEAMLESS",
    },
    {
        "canonical_id": "CAN-0006203",
        "item_type": "PIPE_SEAMLESS",
        "size_nb_mm": 150.0,
        "size_inch": '6"',
        "dn_code": "DN150",
        "pressure_class": 0,
        "metallurgy": "ASTM A106 GR.B",
        "facing_end": "BW",
        "standard": "ASME B36.10M",
        "canonical_description": 'PIPE, SEAMLESS, 6" (DN150), SCH 40, ASTM A106 GR.B, BEVELED ENDS, ASME B36.10M',
        "unspsc_code": "40171502",
        "gem_category_id": "GEM-PIPE-SEAMLESS",
    },
    {
        "canonical_id": "CAN-0006204",
        "item_type": "PIPE_SEAMLESS",
        "size_nb_mm": 200.0,
        "size_inch": '8"',
        "dn_code": "DN200",
        "pressure_class": 0,
        "metallurgy": "ASTM A106 GR.B",
        "facing_end": "BW",
        "standard": "ASME B36.10M",
        "canonical_description": 'PIPE, SEAMLESS, 8" (DN200), SCH 40, ASTM A106 GR.B, BEVELED ENDS, ASME B36.10M',
        "unspsc_code": "40171502",
        "gem_category_id": "GEM-PIPE-SEAMLESS",
    },
    {
        "canonical_id": "CAN-0006205",
        "item_type": "PIPE_SEAMLESS",
        "size_nb_mm": 250.0,
        "size_inch": '10"',
        "dn_code": "DN250",
        "pressure_class": 0,
        "metallurgy": "ASTM A106 GR.B",
        "facing_end": "BW",
        "standard": "ASME B36.10M",
        "canonical_description": 'PIPE, SEAMLESS, 10" (DN250), SCH 40, ASTM A106 GR.B / API 5L, BEVELED ENDS, ASME B36.10M',
        "unspsc_code": "40171502",
        "gem_category_id": "GEM-PIPE-SEAMLESS",
    },
    {
        "canonical_id": "CAN-0006206",
        "item_type": "PIPE_SEAMLESS",
        "size_nb_mm": 250.0,
        "size_inch": '10"',
        "dn_code": "DN250",
        "pressure_class": 0,
        "metallurgy": "ASTM A106 GR.B",
        "facing_end": "BW",
        "standard": "ASME B36.10M",
        "canonical_description": 'PIPE, SEAMLESS, 10" (DN250), SCH 80, ASTM A106 GR.B / API 5L, BEVELED ENDS, ASME B36.10M',
        "unspsc_code": "40171502",
        "gem_category_id": "GEM-PIPE-SEAMLESS",
    },
    {
        "canonical_id": "CAN-0006207",
        "item_type": "PIPE_SEAMLESS",
        "size_nb_mm": 250.0,
        "size_inch": '10"',
        "dn_code": "DN250",
        "pressure_class": 0,
        "metallurgy": "ASTM A333 GR.6",
        "facing_end": "BW",
        "standard": "ASME B36.10M",
        "canonical_description": 'PIPE, SEAMLESS, 10" (DN250), SCH 40, ASTM A333 GR.6 (LOW TEMPERATURE), BEVELED ENDS, ASME B36.10M',
        "unspsc_code": "40171502",
        "gem_category_id": "GEM-PIPE-SEAMLESS",
    },
    {
        "canonical_id": "CAN-0006208",
        "item_type": "PIPE_SEAMLESS",
        "size_nb_mm": 250.0,
        "size_inch": '10"',
        "dn_code": "DN250",
        "pressure_class": 0,
        "metallurgy": "ASTM A312 TP316L",
        "facing_end": "BW",
        "standard": "ASME B36.19M",
        "canonical_description": 'PIPE, SEAMLESS, 10" (DN250), SCH 40S, ASTM A312 TP316L, BEVELED ENDS, ASME B36.19M',
        "unspsc_code": "40171502",
        "gem_category_id": "GEM-PIPE-SEAMLESS",
    },
    {
        "canonical_id": "CAN-0006209",
        "item_type": "PIPE_SEAMLESS",
        "size_nb_mm": 300.0,
        "size_inch": '12"',
        "dn_code": "DN300",
        "pressure_class": 0,
        "metallurgy": "ASTM A106 GR.B",
        "facing_end": "BW",
        "standard": "ASME B36.10M",
        "canonical_description": 'PIPE, SEAMLESS, 12" (DN300), SCH 40, ASTM A106 GR.B, BEVELED ENDS, ASME B36.10M',
        "unspsc_code": "40171502",
        "gem_category_id": "GEM-PIPE-SEAMLESS",
    },
]

# Check existing IDs
existing_ids = set()
with open(canonical_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        existing_ids.add(row["canonical_id"])

with open(canonical_path, "a", encoding="utf-8", newline="") as f:
    fieldnames = [
        "canonical_id", "item_type", "size_nb_mm", "size_inch", "dn_code",
        "pressure_class", "metallurgy", "facing_end", "standard",
        "canonical_description", "unspsc_code", "gem_category_id"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    for c in new_canonicals:
        if c["canonical_id"] not in existing_ids:
            writer.writerow(c)
            print(f"Appended {c['canonical_id']} to canonical_master.csv")

# 2. Append pipes to CPSE catalogs
ongc_pipes = [
    {
        "local_code": "ONGC-MAT-0004182",
        "cpse": "ONGC",
        "raw_description": 'PIPE, SEAMLESS, 10" (DN250), SCH 40, ASTM A106 GR.B / API 5L, BE, ASME B36.10M',
        "canonical_id": "CAN-0006205",
        "depot_id": "DEPOT-ONGC-HZR",
        "depot_location": "Hazira Gas Processing Plant, Gujarat",
        "quantity": 45,
        "unit_cost_inr": 32500,
        "idle_days": 190,
        "extracted_item_type": "PIPE_SEAMLESS",
        "extracted_size_nb_mm": 250.0,
        "extracted_pressure_class": 0,
        "extracted_metallurgy": "ASTM A106 GR.B",
        "extracted_facing": "BW",
        "extracted_standard": "ASME B36.10M",
    },
    {
        "local_code": "ONGC-MAT-0004183",
        "cpse": "ONGC",
        "raw_description": 'PIPE SEAMLESS 10" SCH 80 ASTM A106 GR.B ASME B36.10M',
        "canonical_id": "CAN-0006206",
        "depot_id": "DEPOT-ONGC-URN",
        "depot_location": "Uran Plant, Maharashtra",
        "quantity": 28,
        "unit_cost_inr": 48000,
        "idle_days": 140,
        "extracted_item_type": "PIPE_SEAMLESS",
        "extracted_size_nb_mm": 250.0,
        "extracted_pressure_class": 0,
        "extracted_metallurgy": "ASTM A106 GR.B",
        "extracted_facing": "BW",
        "extracted_standard": "ASME B36.10M",
    },
]

bpcl_pipes = [
    {
        "local_code": "BPCL-SAP-0007214",
        "cpse": "BPCL",
        "raw_description": 'PIPE SEAMLESS 10 INCH NB SCH 40 ASTM A106 GR.B BEVELED ENDS ASME B36.10M',
        "canonical_id": "CAN-0006205",
        "depot_id": "DEPOT-BPCL-MUM",
        "depot_location": "Mumbai Refinery, Mahul, Maharashtra",
        "quantity": 36,
        "unit_cost_inr": 32500,
        "idle_days": 165,
        "extracted_item_type": "PIPE_SEAMLESS",
        "extracted_size_nb_mm": 250.0,
        "extracted_pressure_class": 0,
        "extracted_metallurgy": "ASTM A106 GR.B",
        "extracted_facing": "BW",
        "extracted_standard": "ASME B36.10M",
    },
    {
        "local_code": "BPCL-SAP-0007215",
        "cpse": "BPCL",
        "raw_description": 'PIPE SMLS 10" SCH 40S ASTM A312 TP316L ASME B36.19M',
        "canonical_id": "CAN-0006208",
        "depot_id": "DEPOT-BPCL-KCH",
        "depot_location": "Kochi Refinery, Kerala",
        "quantity": 18,
        "unit_cost_inr": 86000,
        "idle_days": 110,
        "extracted_item_type": "PIPE_SEAMLESS",
        "extracted_size_nb_mm": 250.0,
        "extracted_pressure_class": 0,
        "extracted_metallurgy": "ASTM A312 TP316L",
        "extracted_facing": "BW",
        "extracted_standard": "ASME B36.19M",
    },
]

iocl_pipes = [
    {
        "local_code": "IOCL-MM-0005510",
        "cpse": "IOCL",
        "raw_description": 'PIPE SEAMLESS 10" SCH 40 ASTM A333 GR.6 LOW TEMP SERVICE ASME B36.10M',
        "canonical_id": "CAN-0006207",
        "depot_id": "DEPOT-IOCL-KHL",
        "depot_location": "Gujarat Refinery (Koyali), Vadodara",
        "quantity": 24,
        "unit_cost_inr": 54000,
        "idle_days": 220,
        "extracted_item_type": "PIPE_SEAMLESS",
        "extracted_size_nb_mm": 250.0,
        "extracted_pressure_class": 0,
        "extracted_metallurgy": "ASTM A333 GR.6",
        "extracted_facing": "BW",
        "extracted_standard": "ASME B36.10M",
    },
    {
        "local_code": "IOCL-MM-0005511",
        "cpse": "IOCL",
        "raw_description": 'PIPE SEAMLESS 10" (DN250) SCH 40 ASTM A106 GR.B BEVELED ENDS ASME B36.10M',
        "canonical_id": "CAN-0006205",
        "depot_id": "DEPOT-IOCL-PNP",
        "depot_location": "Panipat Refinery, Haryana",
        "quantity": 50,
        "unit_cost_inr": 32500,
        "idle_days": 95,
        "extracted_item_type": "PIPE_SEAMLESS",
        "extracted_size_nb_mm": 250.0,
        "extracted_pressure_class": 0,
        "extracted_metallurgy": "ASTM A106 GR.B",
        "extracted_facing": "BW",
        "extracted_standard": "ASME B36.10M",
    },
]

def append_to_catalog(cat_path: Path, items: list):
    existing = set()
    with open(cat_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            existing.add(r["local_code"])
    with open(cat_path, "a", encoding="utf-8", newline="") as f:
        fieldnames = [
            "local_code", "cpse", "raw_description", "canonical_id",
            "depot_id", "depot_location", "quantity", "unit_cost_inr",
            "idle_days", "extracted_item_type", "extracted_size_nb_mm",
            "extracted_pressure_class", "extracted_metallurgy",
            "extracted_facing", "extracted_standard"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for it in items:
            if it["local_code"] not in existing:
                writer.writerow(it)
                print(f"Appended {it['local_code']} to {cat_path.name}")

append_to_catalog(Path("data/mock_cpes_catalogs/ongc_materials.csv"), ongc_pipes)
append_to_catalog(Path("data/mock_cpes_catalogs/bpcl_materials.csv"), bpcl_pipes)
append_to_catalog(Path("data/mock_cpes_catalogs/iocl_materials.csv"), iocl_pipes)
print("Pipes added successfully to catalogs!")
