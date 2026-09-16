import csv
from pathlib import Path

pipe_samples = [
    # 2 inch
    {
        'local_code': 'ONGC-MAT-0004184',
        'cpse': 'ONGC',
        'raw_description': 'PIPE, SEAMLESS, 2" (DN50), SCH 40, ASTM A106 GR.B, BEVELED ENDS, ASME B36.10M',
        'canonical_id': 'CAN-0006201',
        'depot_id': 'DEPOT-ONGC-HZR',
        'depot_location': 'Hazira Gas Processing Plant, Gujarat',
        'quantity': 120,
        'unit_cost_inr': 4800,
        'idle_days': 160,
        'extracted_item_type': 'PIPE_SEAMLESS',
        'extracted_size_nb_mm': 50.0,
        'extracted_pressure_class': 0,
        'extracted_metallurgy': 'ASTM A106 GR.B',
        'extracted_facing': 'BW',
        'extracted_standard': 'ASME B36.10M'
    },
    {
        'local_code': 'BPCL-SAP-0007216',
        'cpse': 'BPCL',
        'raw_description': 'PIPE SEAMLESS 2 INCH SCH 40 CS ASTM A106-B ASME B36.10',
        'canonical_id': 'CAN-0006201',
        'depot_id': 'DEPOT-BPCL-MUM',
        'depot_location': 'Mumbai Refinery, Mahul, Maharashtra',
        'quantity': 95,
        'unit_cost_inr': 4800,
        'idle_days': 210,
        'extracted_item_type': 'PIPE_SEAMLESS',
        'extracted_size_nb_mm': 50.0,
        'extracted_pressure_class': 0,
        'extracted_metallurgy': 'ASTM A106 GR.B',
        'extracted_facing': 'BW',
        'extracted_standard': 'ASME B36.10M'
    },
    {
        'local_code': 'IOCL-MM-0005512',
        'cpse': 'IOCL',
        'raw_description': 'PIPE SEAMLESS 2" (DN50) SCH 40 ASTM A106 GR.B BE ASME B36.10M',
        'canonical_id': 'CAN-0006201',
        'depot_id': 'DEPOT-IOCL-PNP',
        'depot_location': 'Panipat Refinery, Haryana',
        'quantity': 140,
        'unit_cost_inr': 4800,
        'idle_days': 90,
        'extracted_item_type': 'PIPE_SEAMLESS',
        'extracted_size_nb_mm': 50.0,
        'extracted_pressure_class': 0,
        'extracted_metallurgy': 'ASTM A106 GR.B',
        'extracted_facing': 'BW',
        'extracted_standard': 'ASME B36.10M'
    },
    # 4 inch
    {
        'local_code': 'ONGC-MAT-0004185',
        'cpse': 'ONGC',
        'raw_description': 'PIPE, SEAMLESS, 4" (DN100), SCH 40, ASTM A106 GR.B, BEVELED ENDS, ASME B36.10M',
        'canonical_id': 'CAN-0006202',
        'depot_id': 'DEPOT-ONGC-URN',
        'depot_location': 'Uran Plant, Maharashtra',
        'quantity': 80,
        'unit_cost_inr': 9600,
        'idle_days': 175,
        'extracted_item_type': 'PIPE_SEAMLESS',
        'extracted_size_nb_mm': 100.0,
        'extracted_pressure_class': 0,
        'extracted_metallurgy': 'ASTM A106 GR.B',
        'extracted_facing': 'BW',
        'extracted_standard': 'ASME B36.10M'
    },
    {
        'local_code': 'BPCL-SAP-0007217',
        'cpse': 'BPCL',
        'raw_description': 'PIPE SEAMLESS 4 INCH SCH 40 CS ASTM A106-B ASME B36.10',
        'canonical_id': 'CAN-0006202',
        'depot_id': 'DEPOT-BPCL-KCH',
        'depot_location': 'Kochi Refinery, Kerala',
        'quantity': 65,
        'unit_cost_inr': 9600,
        'idle_days': 130,
        'extracted_item_type': 'PIPE_SEAMLESS',
        'extracted_size_nb_mm': 100.0,
        'extracted_pressure_class': 0,
        'extracted_metallurgy': 'ASTM A106 GR.B',
        'extracted_facing': 'BW',
        'extracted_standard': 'ASME B36.10M'
    },
    {
        'local_code': 'IOCL-MM-0005513',
        'cpse': 'IOCL',
        'raw_description': 'PIPE SEAMLESS 4" (DN100) SCH 40 ASTM A106 GR.B BE ASME B36.10M',
        'canonical_id': 'CAN-0006202',
        'depot_id': 'DEPOT-IOCL-KHL',
        'depot_location': 'Gujarat Refinery (Koyali), Vadodara',
        'quantity': 110,
        'unit_cost_inr': 9600,
        'idle_days': 185,
        'extracted_item_type': 'PIPE_SEAMLESS',
        'extracted_size_nb_mm': 100.0,
        'extracted_pressure_class': 0,
        'extracted_metallurgy': 'ASTM A106 GR.B',
        'extracted_facing': 'BW',
        'extracted_standard': 'ASME B36.10M'
    },
    # 6 inch
    {
        'local_code': 'ONGC-MAT-0004186',
        'cpse': 'ONGC',
        'raw_description': 'PIPE, SEAMLESS, 6" (DN150), SCH 40, ASTM A106 GR.B, BEVELED ENDS, ASME B36.10M',
        'canonical_id': 'CAN-0006203',
        'depot_id': 'DEPOT-ONGC-HZR',
        'depot_location': 'Hazira Gas Processing Plant, Gujarat',
        'quantity': 60,
        'unit_cost_inr': 15800,
        'idle_days': 200,
        'extracted_item_type': 'PIPE_SEAMLESS',
        'extracted_size_nb_mm': 150.0,
        'extracted_pressure_class': 0,
        'extracted_metallurgy': 'ASTM A106 GR.B',
        'extracted_facing': 'BW',
        'extracted_standard': 'ASME B36.10M'
    },
    {
        'local_code': 'BPCL-SAP-0007218',
        'cpse': 'BPCL',
        'raw_description': 'PIPE SMLS 6 IN SCH 40 CS ASTM A106-B ASME B36.10',
        'canonical_id': 'CAN-0006203',
        'depot_id': 'DEPOT-BPCL-MUM',
        'depot_location': 'Mumbai Refinery, Mahul, Maharashtra',
        'quantity': 45,
        'unit_cost_inr': 15800,
        'idle_days': 150,
        'extracted_item_type': 'PIPE_SEAMLESS',
        'extracted_size_nb_mm': 150.0,
        'extracted_pressure_class': 0,
        'extracted_metallurgy': 'ASTM A106 GR.B',
        'extracted_facing': 'BW',
        'extracted_standard': 'ASME B36.10M'
    },
    {
        'local_code': 'IOCL-MM-0005514',
        'cpse': 'IOCL',
        'raw_description': 'PIPE SEAMLESS 6" (DN150) SCH 40 ASTM A106 GR.B BE ASME B36.10M',
        'canonical_id': 'CAN-0006203',
        'depot_id': 'DEPOT-IOCL-PNP',
        'depot_location': 'Panipat Refinery, Haryana',
        'quantity': 55,
        'unit_cost_inr': 15800,
        'idle_days': 140,
        'extracted_item_type': 'PIPE_SEAMLESS',
        'extracted_size_nb_mm': 150.0,
        'extracted_pressure_class': 0,
        'extracted_metallurgy': 'ASTM A106 GR.B',
        'extracted_facing': 'BW',
        'extracted_standard': 'ASME B36.10M'
    },
    # 8 inch
    {
        'local_code': 'ONGC-MAT-0004187',
        'cpse': 'ONGC',
        'raw_description': 'PIPE, SEAMLESS, 8" (DN200), SCH 40, ASTM A106 GR.B, BEVELED ENDS, ASME B36.10M',
        'canonical_id': 'CAN-0006204',
        'depot_id': 'DEPOT-ONGC-HZR',
        'depot_location': 'Hazira Gas Processing Plant, Gujarat',
        'quantity': 50,
        'unit_cost_inr': 24000,
        'idle_days': 180,
        'extracted_item_type': 'PIPE_SEAMLESS',
        'extracted_size_nb_mm': 200.0,
        'extracted_pressure_class': 0,
        'extracted_metallurgy': 'ASTM A106 GR.B',
        'extracted_facing': 'BW',
        'extracted_standard': 'ASME B36.10M'
    },
    {
        'local_code': 'BPCL-SAP-0007219',
        'cpse': 'BPCL',
        'raw_description': 'PIPE SMLS 8 IN SCH 40 CS ASTM A106-B ASME B36.10',
        'canonical_id': 'CAN-0006204',
        'depot_id': 'DEPOT-BPCL-MUM',
        'depot_location': 'Mumbai Refinery, Mahul, Maharashtra',
        'quantity': 40,
        'unit_cost_inr': 24000,
        'idle_days': 120,
        'extracted_item_type': 'PIPE_SEAMLESS',
        'extracted_size_nb_mm': 200.0,
        'extracted_pressure_class': 0,
        'extracted_metallurgy': 'ASTM A106 GR.B',
        'extracted_facing': 'BW',
        'extracted_standard': 'ASME B36.10M'
    },
    # 12 inch
    {
        'local_code': 'IOCL-MM-0005515',
        'cpse': 'IOCL',
        'raw_description': 'PIPE SEAMLESS 12" (DN300) SCH 40 ASTM A106 GR.B BE ASME B36.10M',
        'canonical_id': 'CAN-0006209',
        'depot_id': 'DEPOT-IOCL-PNP',
        'depot_location': 'Panipat Refinery, Haryana',
        'quantity': 35,
        'unit_cost_inr': 42000,
        'idle_days': 195,
        'extracted_item_type': 'PIPE_SEAMLESS',
        'extracted_size_nb_mm': 300.0,
        'extracted_pressure_class': 0,
        'extracted_metallurgy': 'ASTM A106 GR.B',
        'extracted_facing': 'BW',
        'extracted_standard': 'ASME B36.10M'
    },
]

catalogs_dir = Path("data/mock_cpes_catalogs")
fieldnames = [
    "local_code", "cpse", "raw_description", "canonical_id",
    "depot_id", "depot_location", "quantity", "unit_cost_inr",
    "idle_days", "extracted_item_type", "extracted_size_nb_mm",
    "extracted_pressure_class", "extracted_metallurgy",
    "extracted_facing", "extracted_standard"
]

for item in pipe_samples:
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
print("Additional pipe sizes appended successfully.")
