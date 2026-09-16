import csv
from pathlib import Path

equipment = [
    {
        "cpse": "ONGC",
        "local_code": "ONGC-MAT-0005512",
        "raw_description": "MOTOR FLAMEPROOF 37KW 4P 415V EX D IIC T4 GB 1500RPM FOOT MOUNTED IS/IEC 60079",
        "canonical_id": "CAN-0005512",
        "depot_id": "DEPOT-ONGC-URN",
        "depot_location": "Uran Plant, Maharashtra",
        "quantity": 6,
        "unit_cost_inr": 185000,
        "idle_days": 95,
        "extracted_item_type": "MOTOR_FLAMEPROOF",
        "extracted_size_nb_mm": 0,
        "extracted_pressure_class": 0,
        "extracted_metallurgy": "CAST_IRON",
        "extracted_facing": "",
        "extracted_standard": "IS/IEC 60079"
    },
    {
        "cpse": "BPCL",
        "local_code": "BPCL-SAP-0008891",
        "raw_description": "SEAL MECHANICAL 50MM CARTRIDGE DUAL PRESSURIZED PLAN 53A SIC/SIC API 682",
        "canonical_id": "CAN-0008891",
        "depot_id": "DEPOT-BPCL-MUM",
        "depot_location": "Mumbai Refinery, Mahul, Maharashtra",
        "quantity": 12,
        "unit_cost_inr": 92000,
        "idle_days": 110,
        "extracted_item_type": "MECHANICAL_SEAL",
        "extracted_size_nb_mm": 50.0,
        "extracted_pressure_class": 0,
        "extracted_metallurgy": "SIC/SIC",
        "extracted_facing": "",
        "extracted_standard": "API 682"
    },
    {
        "cpse": "IOCL",
        "local_code": "IOCL-SAP-0004120",
        "raw_description": "BEARING DEEP GROOVE BALL 50X110X27MM C3 CLEARANCE SKF ISO 15 (6310-2RS1/C3)",
        "canonical_id": "CAN-0004120",
        "depot_id": "DEPOT-IOCL-KOY",
        "depot_location": "Gujarat Refinery (Koyali), Vadodara",
        "quantity": 40,
        "unit_cost_inr": 14200,
        "idle_days": 75,
        "extracted_item_type": "BEARING_ROLLER",
        "extracted_size_nb_mm": 50.0,
        "extracted_pressure_class": 0,
        "extracted_metallurgy": "CHROME_STEEL",
        "extracted_facing": "",
        "extracted_standard": "ISO 15"
    }
]

catalogs_dir = Path("data/mock_cpes_catalogs")
fieldnames = [
    "local_code", "cpse", "raw_description", "canonical_id",
    "depot_id", "depot_location", "quantity", "unit_cost_inr",
    "idle_days", "extracted_item_type", "extracted_size_nb_mm",
    "extracted_pressure_class", "extracted_metallurgy",
    "extracted_facing", "extracted_standard"
]

for item in equipment:
    cpse_file = catalogs_dir / f"{item['cpse'].lower()}_materials.csv"
    if not cpse_file.exists():
        continue
    existing = set()
    with open(cpse_file, "r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for r in reader:
            existing.add(r["local_code"])
    if item["local_code"] not in existing:
        with open(cpse_file, "a", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            writer.writerow(item)
            print(f"Appended {item['local_code']} to {cpse_file.name}")

print("Equipment synced successfully.")
