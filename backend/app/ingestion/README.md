# Document Ingestion & OCR Pipeline (`backend/app/ingestion`)

## 1. Overview
The `ingestion` package processes incoming procurement documents—including scanned Mill Test Certificates (MTCs), delivery challans, and PDF purchase orders—converting unstructured visual artifacts into structured material specifications.

---

## 2. Directory Structure

```
backend/app/ingestion/
|-- data_pipeline/               # Catalog streaming and synthetic catalog generation
|   |-- loader.py                # Streaming CSV/JSON catalog ingestion utilities
|   `-- README.md                # Data pipeline documentation
|-- certificate.py               # EN 10204 3.1 Mill Test Certificate tabular parser
|-- ocr_engine.py                # Multi-tier hardware-accelerated OCR engine
|-- pdf_parser.py                # Digital and raster PDF document extractor
|-- storage.py                   # SQLAlchemy database models and audit logging
`-- README.md                    # This file
```

---

## 3. OCR Engine Architecture (`ocr_engine.py`)

Industrial documents in refineries range from pristine vector PDFs to distorted, low-resolution carbon copies and camera snapshots. Samanvay-AI uses a three-tier extraction strategy:

```
                            Input Document (PDF / Image)
                                        |
                   Is digital PDF with embedded text layer?
                                    /        \
                                  Yes         No
                                  /            \
                  Extract via PDFPlumber       Run Image Preprocessing
                  (Sub-20ms text stream)       (Grayscale, contrast adjustment)
                                                        |
                                            Check OS Environment
                                                  /        \
                                            Windows        Linux / macOS
                                              /                \
                             Native Windows Media OCR        PaddleOCR / EasyOCR
                             (Hardware-accelerated           (PyTorch / ONNX CPU)
                              sub-250ms execution)             (500ms - 1200ms)
```

### Why Native Windows Media OCR (`winocr`)?
1. Speed: Executes in under 250 milliseconds per full-page 300 DPI image.
2. Zero GPU Requirement: Uses native Windows Runtime hardware decoders built into the operating system.
3. Offline Operation: Runs completely air-gapped without transmitting sensitive refinery documents to external cloud APIs.

---

## 4. Mill Test Certificate Extraction (`certificate.py`)

A Mill Test Certificate (governed by EN 10204 standard types 3.1 or 2.2) is the legal proof of a material's chemical and mechanical properties.

`certificate.py` implements a tabular parser that extracts:
1. Header Metadata: Certificate number, Purchase Order number, Manufacturer, Heat/Melt number.
2. Governing Standards: ASTM A105, ASTM A182, ASTM A815, ASME B16.5, ASME B16.9.
3. Chemical Analysis:
   - Carbon (C) %
   - Manganese (Mn) %
   - Silicon (Si) %
   - Phosphorus (P) % and Sulfur (S) % (critical for sour service limits)
   - Chromium (Cr) % and Molybdenum (Mo) % (pitting resistance)
4. Mechanical Properties:
   - Yield Strength (MPa or N/mm2)
   - Ultimate Tensile Strength (MPa)
   - Elongation percentage (%)
   - Hardness (Brinell HBW or Rockwell HRC)

---

## 5. Storage Layer & Database Models (`storage.py`)

Database models are managed with SQLAlchemy ORM, configured for SQLite during local development and PostgreSQL in production:

### 1. `ReconciliationAudit`
Stores every standardization action, human review decision, and transfer event:
- `id`: Unique integer primary key.
- `timestamp`: UTC ISO timestamp.
- `source_sku`: Legacy enterprise code.
- `source_cpse`: Enterprise identifier (`IOCL`, `ONGC`, `BPCL`).
- `matched_canonical_id`: Master item identifier.
- `tier`: Assigned equivalence tier.
- `confidence`: Algorithmic confidence score.
- `verified_by_hitl`: Boolean flag indicating whether a human engineer reviewed the item.
- `hitl_officer`: Username or employee ID of the reviewing officer.
- `sha256_hash`: Cryptographic digest over record attributes ensuring tamper-evident auditing.

### 2. `DocumentIngestJob`
Tracks file upload jobs, processing duration, extracted line item counts, and status (`PENDING`, `COMPLETED`, `FAILED`).
