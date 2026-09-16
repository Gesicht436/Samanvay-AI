# Document Ingestion & OCR Pipeline (`backend/app/ingestion`)

## 1. Overview
The `ingestion` package processes incoming procurement documents—including scanned Mill Test Certificates (MTCs), delivery challans, and PDF purchase orders—converting unstructured visual artifacts into structured material specifications, chemical compositions, and mechanical property verifications.

---

## 2. Directory Structure

```
backend/app/ingestion/
|-- data_pipeline/               # Catalog streaming and synthetic catalog generation
|   |-- loader.py                # Streaming CSV/JSON catalog ingestion utilities
|   `-- README.md                # Data pipeline documentation
|-- certificate.py               # EN 10204 3.1/3.2 MTC parser with Carbon Equivalent & ASTM checks
|-- ocr_engine.py                # Multi-tier hardware-accelerated OCR with image preprocessing
|-- pdf_parser.py                # Multi-page parallel PDF document extractor
|-- storage.py                   # SQLAlchemy database models and audit logging
`-- README.md                    # This file
```

---

## 3. OCR Engine Architecture & Image Pre-Processing (`ocr_engine.py`)

Industrial documents in refineries range from pristine vector PDFs to skewed, low-contrast carbon copies, faint dot-matrix receipts, and mobile phone camera photos.

### A. Pre-Processing Pipeline (`preprocess_image_for_ocr`)
Before running optical character recognition, incoming images pass through an automated enhancement pipeline:

1. **Resolution Normalization**:
   - Upscales low-DPI scans to a minimum width of 1,600 pixels using bicubic interpolation, ensuring fine font strokes and decimal points are clearly rendered.
2. **Document Orientation & Auto-Deskewing (`estimate_skew_angle`)**:
   - Computes projection profile variance over rotated angles (-10 to +10 degrees) to correct document tilt before line segmentation.
3. **Contrast & Edge Sharpening**:
   - Applies histogram autocontrast and unsharp-mask sharpening to make faded characters legible.
4. **Adaptive Otsu Binarization**:
   - Converts difficult, stained, or carbon-copy scans into high-contrast binary images when initial passes yield sparse text.

### B. Multi-Tier Engine Cascading & Confidence-Driven Retry
The engine automatically routes through available system runtimes:

```
                            Input Document (PDF / Image)
                                         |
                    Is digital PDF with selectable text?
                                     /        \
                                   Yes         No
                                   /            \
                   Extract via PDFPlumber       Run Image Preprocessing
                   (Sub-20ms text stream)       (Deskew, contrast, Otsu threshold)
                                                         |
                                             Check OS Environment
                                                   /        \
                                             Windows        Linux / macOS
                                               /                \
                              Native Windows Media OCR        PaddleOCR / EasyOCR
                              (Hardware-accelerated           (PyTorch / ONNX CPU)
                               sub-250ms execution)             (500ms - 1200ms)
                                         |
                       Is extracted text sparse (< 35 chars)?
                                     /        \
                                   Yes         No
                                   /            \
                 Apply adaptive binarization   Return parsed text
                 and retry extraction pass
```

---

## 4. Multi-Page Parallel PDF Processing (`pdf_parser.py`)

`pdf_parser.py` implements intelligent dual-path routing:

1. **Fast Path (Digital Vector PDFs)**:
   Extracts text streams and bounding-box tables via `pdfplumber` in under 50 milliseconds without running OCR.
2. **Slow Path (Multi-Page Scanned Documents)**:
   When digital text is absent, the parser renders pages to 300 DPI images and distributes them across a concurrent `ThreadPoolExecutor`. Each page is OCRed in parallel, and results are stitched in sequential page order.

---

## 5. Mill Test Certificate Extraction & Safety Checks (`certificate.py`)

A Mill Test Certificate (governed by EN 10204 standard types 3.1 or 3.2) is the legal proof of a material's chemical and mechanical properties.

### A. Header Metadata & Granular Classification
Extracts core tracking identifiers:
- Certificate Number (`cert_no`), Purchase Order (`po_no`), Heat/Melt Number (`heat_no`), Manufacturer (`manufacturer`).
- Document Sub-Classification:
  - `MTC_EN10204_3_1`: Standard inspection certificate by manufacturer.
  - `MTC_EN10204_3_2`: Third-Party Inspection (TPI) verified certificate (Lloyd's, DNV, TUV, Bureau Veritas).
  - `DELIVERY_CHALLAN_CPSE`: Inward depot dispatch receipt.
  - `PURCHASE_ORDER_STANDARD`: ERP purchase requisition.
  - `VALVE_HYDRO_TEST_REPORT`: Hydrostatic shell/seat test certificate.
  - `FASTENER_QUALITY_CERTIFICATE`: Stud bolt & nut inspection certificate.

### B. Carbon Equivalent (CE) Weldability Calculation
For structural and carbon steel components (e.g., ASTM A105, ASTM A350 LF2), elevated carbon levels reduce weldability and increase cracking risk. The parser automatically computes the International Institute of Welding (IIW) Carbon Equivalent:

$$\text{CE} = \%C + \frac{\%Mn}{6} + \frac{\%Cr + \%Mo + \%V}{5} + \frac{\%Ni + \%Cu}{15}$$

- **Threshold Check**: Standard ASME/ASTM weldability limit is $\text{CE} \le 0.43\%$. If $\text{CE} > 0.43\%$, the parser flags the certificate with `PREHEAT_REQUIRED_HIGH_CE` and attaches a validation warning.

### C. Mechanical Threshold Validation
Cross-validates extracted physical test results against statutory ASTM minimum standards:
- **ASTM A105**: Validates Yield Strength $\ge 250\text{ MPa}$ and Tensile Strength $\ge 485\text{ MPa}$.
- **ASTM A350 LF2**: Validates Yield Strength $\ge 250\text{ MPa}$.
- **ASTM A182 F316**: Validates Yield Strength $\ge 205\text{ MPa}$ ($\ge 170\text{ MPa}$ for 316L).
If values fall below ASTM minimums, the system logs validation warnings for plant engineering review.

### D. Multi-Item Line Extraction
For certificates listing multiple items on a single purchase order, the parser isolates each line item, enriches it with global metallurgy and standard metadata, and runs `extract_attributes()` to produce structured attribute schemas per line.

---

## 6. Storage Layer & Database Models (`storage.py`)

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
Tracks file upload jobs, processing duration, extracted line item counts, document sub-types, and status (`PENDING`, `COMPLETED`, `FAILED`).
