# Catalog Ingestion Pipeline (`backend/app/ingestion/data_pipeline`)

## 1. Overview
The `data_pipeline` subpackage manages the bulk loading, transformation, and ingestion of enterprise procurement catalogs into Samanvay-AI.

Refinery ERP item catalogs frequently contain tens of thousands of rows with inconsistent column headers, duplicate part descriptions, and varied character encodings. This package ensures robust streaming and batch ingestion without running out of server memory.

---

## 2. Directory Structure

```
backend/app/ingestion/data_pipeline/
|-- loader.py                    # Streaming catalog reader and batch processor
`-- README.md                    # This file
```

---

## 3. Streaming Ingestion (`loader.py`)

### Challenges in Legacy Catalog Ingestion
1. Memory Spikes: Attempting to load a 500 MB ERP export CSV into a single Pandas dataframe in memory can exhaust server RAM under concurrent traffic.
2. Encoding Anomalies: Legacy Windows SAP installations frequently export files encoded with `cp1252`, `latin-1`, or UTF-8 with Byte Order Mark (BOM).
3. Missing Fields: Some records omit nominal bore or specify it in millimeters rather than inches, while others omit pressure ratings entirely.

### How `loader.py` Resolves This
- Generator-Based Streaming: Uses Python generators to yield records in configurable batch chunks (default: 500 items per chunk).
- Automatic Encoding Detection: Detects UTF-8 BOM, standard UTF-8, and falls back to `latin-1` transparently.
- Field Mapping Resilience: Flexible dictionary mapping handles variable column headers:
  - `Material Number`, `Item Code`, `MATNR`, `STOCK_NO` -> mapped to `source_sku`.
  - `Description`, `Short Text`, `PO_TEXT`, `MAKTX` -> mapped to `source_description`.
  - `Plant`, `Storage Location`, `WERKS`, `LGORT` -> mapped to `depot_name`.
- Normalization Pipeline: For each streamed row, calls `extract_attributes` from `ner_tagger.py` to populate standardized attributes on the fly.

---

## 4. Usage Example in Scripts or Tasks

```python
from backend.app.ingestion.data_pipeline.loader import stream_catalog_csv

# Process a 100,000-line catalog without exceeding 50 MB memory usage
for batch in stream_catalog_csv("data/raw/iocl_panipat_catalog.csv", chunk_size=500):
    for item in batch:
        # Each item is validated and transformed into standardized Pydantic models
        process_item(item)
```
