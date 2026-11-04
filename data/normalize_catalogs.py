"""
normalize_catalogs.py
Standardizes all CSV catalogs in data/catalogs/ to the Canonical Material Schema (SCMS-27).
Ensures uniform column naming across CPSE ERP catalogs.
"""

import os
import glob
from pathlib import Path
import pandas as pd

from backend.app.contracts.canonical_schema import COLUMN_ALIASES, CANONICAL_COLUMNS


def derive_depot_id(cpse: str, location: str) -> str:
    loc_clean = str(location).split(",")[0].strip().replace(" ", "_").upper()
    return f"{cpse}_{loc_clean}"


def normalize_catalog_csv(file_path: Path):
    print(f"[*] Processing {file_path.name}...")
    df = pd.read_csv(file_path)
    orig_cols = list(df.columns)

    # 1. Rename columns based on canonical alias dictionary
    rename_map = {}
    for col in df.columns:
        clean_col = col.strip().lower()
        if clean_col in COLUMN_ALIASES:
            target = COLUMN_ALIASES[clean_col]
            # Avoid overwriting if target already exists with data
            if target != col and target not in df.columns:
                rename_map[col] = target

    if rename_map:
        df = df.rename(columns=rename_map)

    # 2. Drop redundant legacy columns if canonical version exists
    redundant_pairs = [
        ("gem_category", "gem_category_id"),
        ("mesc_code", "oil_material_code"),
        ("cppp_tender_id", "cppp_tender_ref"),
        ("cpse_name", "cpse"),
        ("raw_description", "description"),
        ("nominal_bore_mm", "size_nb_mm"),
        ("local_code", "sku_code"),
        ("idle_days", "days_idle"),
    ]
    for old_col, new_col in redundant_pairs:
        if old_col in df.columns and new_col in df.columns:
            df = df.drop(columns=[old_col])

    # 3. Ensure CPSE is uppercase
    if "cpse" in df.columns:
        df["cpse"] = df["cpse"].astype(str).str.strip().str.upper()

    # 4. Ensure depot_id exists
    if "depot_id" not in df.columns and "depot_location" in df.columns and "cpse" in df.columns:
        df["depot_id"] = [
            derive_depot_id(c, loc)
            for c, loc in zip(df["cpse"], df["depot_location"])
        ]

    # 5. Ensure status and is_broadcasted_surplus exist
    if "status" not in df.columns and "days_idle" in df.columns:
        statuses = []
        broadcasts = []
        for days in df["days_idle"]:
            d = int(days) if pd.notna(days) else 0
            if d >= 365:
                statuses.append("SURPLUS_DECLARED")
                broadcasts.append(True)
            elif d >= 180:
                statuses.append("POTENTIAL_SURPLUS")
                broadcasts.append(True)
            else:
                statuses.append("TO_BE_CONSUMED")
                broadcasts.append(False)
        df["status"] = statuses
        df["is_broadcasted_surplus"] = broadcasts

    df.to_csv(file_path, index=False)
    print(f"[+] Successfully normalized {file_path.name}: {len(df)} rows, columns: {list(df.columns)}")


def main():
    catalogs_dir = Path(__file__).resolve().parent / "catalogs"
    for csv_file in catalogs_dir.glob("*.csv"):
        normalize_catalog_csv(csv_file)


if __name__ == "__main__":
    main()
