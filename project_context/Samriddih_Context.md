# Document Intelligence & OCR Ingestion Pipeline Workflow

**Role:** Document Intelligence & Ingestion Lead (Smariddih)

**Primary Directory:** `backend/app/ingestion/`

**Target Environment:** Python 3.14, PaddleOCR, PyMuPDF (`fitz`), Pillow, Pydantic v2

---

### Objective & Architectural Role

Your mission is to build the multi-modal intake pipeline for **Samanvay-AI (BharatCodex)**.

CPSE procurement data arrives from physical operations in messy formats: scanned Mill Test Certificates (MTCs), equipment nameplate photos, delivery challans, and legacy scanned invoices.

You own the upstream extraction pipeline:

1. **Dual-Path Text Extraction:** Fast digital extraction for native PDFs, falling back to deep learning OCR for low-resolution, scanned documents.

2. **Key-Value Parsing:** Isolate physical and metallurgical properties (Heat Number, Grade, Tensile Strength, Dimensions) from tabular certificate layouts.

3. **Downstream Handoff:** Clean, normalize, and hand over extracted raw text directly to Hariom’s NER module (`ner_tagger.py`) and Mayank’s FastAPI ingestion router.

```
Incoming Document (Scanned MTC PDF, Nameplate Image, Invoice)
                           │
                           ▼
            ┌──────────────────────────────┐
            │ TASK 1: DUAL-PATH EXTRACTION │
            │      (`pdf_parser.py`)       │
            └──────────────┬───────────────┘
                           │
           Is document digitally selectable?
              ├── YES ──► Extract text directly via PyMuPDF (Fast Path)
              └── NO  ──► Convert pages to images ──┐
                                                    ▼
                                     ┌──────────────────────────────┐
                                     │  TASK 2: PADDLEOCR ENGINE    │
                                     │      (`ocr_engine.py`)       │
                                     │ • Text Angle Classification  │
                                     │ • Bounding Box Detection     │
                                     │ • Word Recognition           │
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
                                                    ▼
                     Expose clean text string & certificate dictionary
                     to Hariom (NER) and Mayank (FastAPI router)

```

---

### Task 1: Dual-Path Document Extraction Engine (`pdf_parser.py`)

In enterprise settings, parsing every PDF through heavy OCR models causes major bottlenecks. You will implement a dual-path routing mechanism:

* **Fast Path (Digital PDFs):**
* Use `PyMuPDF` (`fitz`) to inspect page streams.
* If valid text blocks are detected (`page.get_text("text").strip()`), extract the text immediately without running neural networks ($<50\text{ ms}$ latency).

* **Slow Path (Scanned Images & Poor Quality PDFs):**
* If the page contains only raster images or empty text streams, render the page to a high-DPI image (`page.get_pixmap(dpi=300)`).
* Send the rendered image directly into your PaddleOCR pipeline.

---

### Task 2: Robust OCR Extraction (`ocr_engine.py`)

For scanned delivery receipts, physical MTCs, and equipment nameplate photographs, use **PaddleOCR** (PP-OCRv4).

* **Key Configurations:**
* **Text Direction:** Enable `use_angle_cls=True` to automatically rotate sideways or upside-down mobile scans.

* **Confidence Filtering:** Discard low-confidence character detections ($\text{confidence} < 0.60$).
* **Bounding Box Merging:** Industrial codes often contain spaces or hyphens that get split into multiple bounding boxes (e.g., `["ASTM", "A105"]`). Write a line-reconstruction heuristic that sorts boxes by vertical coordinate ($Y$), then merges horizontally adjacent boxes ($X$).

```python
from paddleocr import PaddleOCR
import numpy as np

ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

def extract_text_from_image(image_bytes: bytes) -> str:
    result = ocr.ocr(image_bytes, cls=True)
    extracted_lines = []
    
    if not result or result[0] is None:
        return ""
        
    for line in result[0]:
        text, confidence = line[1]
        if confidence >= 0.60:
            extracted_lines.append(text)
            
    return " ".join(extracted_lines)

```

---

### Task 3: Certificate & Table Layout Parser (`certificate.py`)

Mill Test Certificates (MTCs) follow structured tabular standards (EN 10204 3.1 / 3.2). Procurement teams verify them to ensure materials match original plant requisitions.

* **Target Fields to Extract from MTCs:**
* **Product Description:** (e.g., `WELD NECK FLANGE 4" 300# RF`)

* **Material Specification / Grade:** (e.g., `ASTM A105N`, `A350 LF2`, `SS316L`)

* **Heat Number / Batch Code:** Key traceability identifier.
* **Standard:** `ASME B16.5`, `NACE MR0175`

* **Implementation Strategy:**
* Use coordinate-based heuristic grouping or regex-anchored window extraction (e.g., locate `"HEAT NO"`, `"SPECIFICATION"`, `"GRADE"` and read the text directly to the right or below the anchor).

---

### Task 4: Directory Deliverables & Interface Contracts

You will work strictly within `backend/app/ingestion/`:

```
backend/app/ingestion/
├── __init__.py
├── ocr_engine.py         # PaddleOCR wrapper with image rotation & confidence thresholds
├── pdf_parser.py         # Dual-path router (PyMuPDF fast path vs. image rendering)
├── certificate.py        # Table and MTC key-value extraction rules
└── normalizer.py         # Strips noise, trailing symbols, non-ASCII characters

```

**Interface Signatures:**

```python
# ingestion/pdf_parser.py
def process_document(file_bytes: bytes, filename: str) -> ExtractedDocumentResult:
    """
    Determines file type (PDF vs. image). 
    Extracts raw text via PyMuPDF or routes to PaddleOCR.
    Returns structured text and detected certificate attributes.
    """
    ...

# ingestion/ocr_engine.py
def run_ocr(image_input: bytes | np.ndarray) -> str:
    """Runs PaddleOCR on image input and returns reconstructed, cleaned text."""
    ...

```

---

### Anticipated Clarifying Questions & Your Direct Answers

* **Q: "Why PaddleOCR instead of Tesseract?"**
**A:** Tesseract struggles heavily with rotated photos, crumpled paper, and skewed plant nameplates. PaddleOCR (PP-OCRv4) has built-in text-angle classification, is lightweight, and runs inference significantly faster on CPU.
* **Q: "Where do I get sample MTCs and scanned invoices to test on?"**
**A:** Shaurya is collecting and generating sample PDFs in `data/raw/`. You can also test using standard Google-searchable sample ASME MTC PDFs or equipment nameplate images.
* **Q: "Do I need to build the upload web page?"**
**A:** No. Ranvijay will build the drag-and-drop frontend upload component in Next.js, and Mayank will build the FastAPI upload endpoint (`POST /api/v1/ingest/document`). Your code will be called by Mayank's route to parse the uploaded file and return the extracted text string.
