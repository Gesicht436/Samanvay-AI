# Document Intelligence & OCR Ingestion Pipeline Workflow

**Role:** Document Intelligence & OCR Lead (Samriddih)

**Collaborators:**
* **Ranvijay** (Collaborates with you to persist extracted document text & parsed metadata into PostgreSQL)
* **Mayank** (Builds FastAPI document ingestion endpoint & manages database engine)
* **Hariom** (Downstream consumer of extracted text for NER & feature engineering)

**Primary Directory:** `backend/app/ingestion/`

**Target Environment:** Python 3.14, PaddleOCR (PP-OCRv4), PyMuPDF (`fitz`), Pillow, Pydantic v2

---

### Objective & Architectural Role

Your mission is to build the multi-modal intake pipeline for **Samanvay-AI (BharatCodex)**.

CPSE procurement data arrives from physical operations in messy formats: scanned Mill Test Certificates (MTCs), equipment nameplate photos, delivery challans, and legacy scanned invoices.

You own the **Document Intelligence & OCR Extraction** pipeline:
1. **Dual-Path Text Extraction:** Fast digital extraction for native PDFs via PyMuPDF ($<50\text{ ms}$), falling back to PaddleOCR for low-resolution, scanned, or tilted documents ($<2\text{ s}$).
2. **Key-Value Parsing:** Isolate physical and metallurgical properties (Heat Number, Grade, Tensile Strength, Dimensions, Standard) from tabular certificate layouts (EN 10204 3.1).
3. **Database Persistence (with Ranvijay):** Collaborate with Ranvijay to store the extracted text and structured JSON metadata in PostgreSQL for full auditability.
4. **Downstream Handoff:** Hand over clean, normalized text to Hariom’s NER module (`ner_tagger.py`) and Mayank’s FastAPI ingestion router.

```
Incoming Document (Scanned MTC PDF, Nameplate Image, Delivery Slip)
                           │
                           ▼
            ┌──────────────────────────────┐
            │ TASK 1: DUAL-PATH EXTRACTION │
            │      (`pdf_parser.py`)       │
            └──────────────┬───────────────┘
                           │
           Is document digitally selectable?
              ├── YES ──► Extract text directly via PyMuPDF (Fast Path <50ms)
              └── NO  ──► Convert pages to 300 DPI images ──┐
                                                            ▼
                                             ┌──────────────────────────────┐
                                             │  TASK 2: PADDLEOCR ENGINE    │
                                             │      (`ocr_engine.py`)       │
                                             │ • Text Angle Classification  │
                                             │ • Bounding Box Stitching     │
                                             │ • Character Recognition      │
                                             └──────────────┬───────────────┘
                                                            │
                                                            ▼
                                             ┌──────────────────────────────┐
                                             │  TASK 3: MTC / KV PARSER     │
                                             │      (`certificate.py`)      │
                                             │ • Table layout reconstruction│
                                             │ • Heat No, Spec, Metallurgy  │
                                             └──────────────┬───────────────┘
                                                            │
                            ┌───────────────────────────────┴───────────────────────────────┐
                            ▼                                                               ▼
             [With Ranvijay: Storage]                                        [To Hariom & Mayank]
             Persist text & metadata into                                    Feed text string to DeBERTa NER
             PostgreSQL (`ingested_documents`)                               and FastAPI Ingest Router
```

---

### Step-by-Step Implementation Guide

#### Task 1: Dual-Path Document Extraction Engine (`backend/app/ingestion/pdf_parser.py`)
In enterprise settings, parsing every PDF through heavy OCR models causes major bottlenecks. Implement a dual-path routing mechanism:
* **Fast Path (Digital PDFs):**
  * Use `PyMuPDF` (`fitz`) to inspect page streams.
  * If selectable text blocks exist (`len(page.get_text("text").strip()) > 30`), extract text immediately ($<50\text{ ms}$).
* **Slow Path (Scanned Images & Low-Quality PDFs):**
  * If the page contains only raster images or empty text streams, render the page to a 300-DPI image (`page.get_pixmap(dpi=300)`).
  * Send the rendered image directly into your PaddleOCR pipeline.

#### Task 2: Robust OCR Extraction (`backend/app/ingestion/ocr_engine.py`)
For scanned delivery receipts, physical MTCs, and equipment nameplate photographs, use **PaddleOCR** (PP-OCRv4):
* **Text Direction:** Enable `use_angle_cls=True` to automatically rotate sideways or upside-down mobile scans.
* **Confidence Filtering:** Discard low-confidence character detections ($\text{confidence} < 0.60$).
* **Bounding Box Merging:** Industrial codes often contain hyphens or spaces that get split (e.g., `["ASTM", "A105"]`). Sort boxes by vertical coordinate ($Y$), then merge horizontally adjacent boxes ($X$).

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

def extract_text_from_image(image_bytes: bytes) -> str:
    result = ocr.ocr(image_bytes, cls=True)
    if not result or result[0] is None:
        return ""
    extracted_lines = []
    for line in result[0]:
        text, confidence = line[1]
        if confidence >= 0.60:
            extracted_lines.append(text)
    return " ".join(extracted_lines)
```

#### Task 3: Certificate & Table Layout Parser (`backend/app/ingestion/certificate.py`)
Mill Test Certificates follow structured tabular standards (EN 10204 3.1 / 3.2):
* **Target Fields to Extract:**
  * **Product Description:** (e.g., `WELD NECK FLANGE 4" 300# RF`)
  * **Material Specification / Grade:** (e.g., `ASTM A105N`, `A350 LF2`, `SS316L`)
  * **Heat Number / Batch Code:** Key traceability identifier (e.g., `HT-98421-B`)
  * **Governing Standard:** (e.g., `ASME B16.5`, `API 6D`)
  * **Quantity & Chemical/Mechanical summary**
* **Verification Fixtures:** Benchmark against the 5 sample PDFs in [`data/raw/`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/raw/) and verify outputs against [`data/raw/sample_mtc_ground_truth.json`](file:///C:/Users/mayan/Development/Hackathons/Samanvay-AI/data/raw/sample_mtc_ground_truth.json).

#### Task 4: Database Storage Collaboration (with Ranvijay)
* Once raw text and metadata dictionary are parsed, call Ranvijay's `save_extracted_document(db, filename, raw_text, metadata)` to store them in PostgreSQL (`ingested_documents` table).

---

### File Deliverables & Directory Layout

Work strictly inside `backend/app/ingestion/`:

```
backend/app/ingestion/
├── __init__.py
├── ocr_engine.py         # PaddleOCR wrapper with image rotation & confidence filtering
├── pdf_parser.py         # Dual-path router (PyMuPDF fast path vs. image rendering)
├── certificate.py        # EN 10204 3.1 table & MTC key-value extraction rules
├── normalizer.py         # Strips noise, non-ASCII characters & whitespace anomalies
└── storage.py            # PostgreSQL document persistence helper (built with Ranvijay)
```

**Interface Signatures:**
```python
# ingestion/pdf_parser.py
def process_document(file_bytes: bytes, filename: str) -> dict:
    """
    Routes PDF/image through PyMuPDF or PaddleOCR.
    Returns dict containing 'raw_text', 'parsed_metadata', and 'confidence'.
    """
    ...

# ingestion/ocr_engine.py
def run_ocr(image_bytes: bytes) -> str:
    """Runs PaddleOCR on image bytes with angle correction and returns reconstructed text."""
    ...
```

---

### Team Collaboration & Handoffs
1. **With Ranvijay:** You extract the text and certificate structure; Ranvijay helps you persist it into PostgreSQL.
2. **With Mayank:** Mayank's `POST /api/v1/ingest/document` endpoint directly invokes your `process_document()` function.
3. **To Hariom:** The cleaned `raw_text` string is handed to Hariom's `extract_attributes()` to extract mechanical engineering slots.
