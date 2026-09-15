"""
Streaming Batch Catalog Ingestion Loader.
Streams large CSV and Excel (.xlsx) ERP dumps with automated column header normalization.
"""

import io
import csv
import logging
from typing import Generator, List, Dict, Any, Union
import pandas as pd
from backend.app.ml.ner_tagger import extract_attributes

logger = logging.getLogger(__name__)

# Fuzzy ERP column header mapping
HEADER_MAPPING = {
    # Description
    "material_desc": "raw_description",
    "material_description": "raw_description",
    "item_description": "raw_description",
    "item_desc": "raw_description",
    "short_text": "raw_description",
    "description": "raw_description",
    "material text": "raw_description",
    "mat_desc": "raw_description",
    
    # SKU / Item Code
    "material_code": "local_code",
    "material_no": "local_code",
    "item_code": "local_code",
    "local_code": "local_code",
    "part_no": "local_code",
    "sku": "local_code",
    "sku_code": "local_code",
    
    # Depot / Plant Location
    "plant": "depot_location",
    "depot": "depot_location",
    "depot_location": "depot_location",
    "location": "depot_location",
    "warehouse": "depot_location",
    
    # Quantity
    "quantity": "quantity",
    "qty": "quantity",
    "stock": "quantity",
    "available_qty": "quantity",
    "stock_qty": "quantity",
    
    # Unit Cost
    "unit_cost": "unit_cost_inr",
    "unit_cost_inr": "unit_cost_inr",
    "cost": "unit_cost_inr",
    "unit_price": "unit_cost_inr",
    "price": "unit_cost_inr",
    
    # Idle Days
    "idle_days": "idle_days",
    "days_idle": "idle_days",
    "aging_days": "idle_days",
}


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes messy column headers into canonical names and ensures uniqueness."""
    rename_dict = {}
    seen_cols = set()
    for col in df.columns:
        clean_col = str(col).strip().lower().replace(" ", "_")
        target_name = col
        if clean_col in HEADER_MAPPING:
            target_name = HEADER_MAPPING[clean_col]
        else:
            # Substring matching heuristics
            if "desc" in clean_col or "text" in clean_col:
                target_name = "raw_description"
            elif "code" in clean_col or "sku" in clean_col or "part" in clean_col:
                target_name = "local_code"
            elif "plant" in clean_col or "depot" in clean_col:
                target_name = "depot_location"
            elif "qty" in clean_col or "stock" in clean_col:
                target_name = "quantity"
            elif "cost" in clean_col or "price" in clean_col:
                target_name = "unit_cost_inr"
            elif "idle" in clean_col or "aging" in clean_col:
                target_name = "idle_days"

        # Ensure unique column names
        final_name = target_name
        suffix = 1
        while final_name in seen_cols:
            final_name = f"{target_name}_{suffix}"
            suffix += 1
        seen_cols.add(final_name)
        rename_dict[col] = final_name

    df = df.rename(columns=rename_dict)
    return df


def stream_catalog_batches(
    file_content: Union[bytes, str],
    filename: str,
    batch_size: int = 100
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Streaming generator that reads CSV/Excel files in memory and yields batches of normalized rows.
    """
    is_excel = filename.lower().endswith((".xlsx", ".xls"))
    
    if isinstance(file_content, bytes):
        stream = io.BytesIO(file_content)
    else:
        stream = open(file_content, "rb")

    try:
        if is_excel:
            df = pd.read_excel(stream)
            df = normalize_headers(df)
            records = df.to_dict(orient="records")
            for i in range(0, len(records), batch_size):
                chunk = records[i:i + batch_size]
                # Enrich with NER attribute parsing
                for item in chunk:
                    desc = str(item.get("raw_description", ""))
                    item["extracted_attributes"] = extract_attributes(desc).model_dump()
                yield chunk
        else:
            # Stream CSV in chunks using pandas
            for chunk_df in pd.read_csv(stream, chunksize=batch_size):
                chunk_df = normalize_headers(chunk_df)
                chunk = chunk_df.to_dict(orient="records")
                for item in chunk:
                    desc = str(item.get("raw_description", ""))
                    item["extracted_attributes"] = extract_attributes(desc).model_dump()
                yield chunk

    finally:
        if not isinstance(file_content, bytes):
            stream.close()
