# Ingestion

`OCR/pipeline.py` accepts uploaded bytes directly. PDFs route independently per page: native text stays on PyMuPDF while image-only pages are rasterized at 300 DPI and preprocessed before OCR. PaddleOCR is primary, with EasyOCR fallback. Per-page methods, OCR engines, and raster resolution are included in the document response and summarized by the dashboard.

`certificate.py` converts extracted text into the MTC ground-truth contract, including labelled chemical-composition values, header/value chemistry tables, and mechanical-property readings. Manufacturer and TPI/inspection-agency detections are returned as lists as well as engineering attributes. The ingest metadata includes `chemical_composition` and `mechanical_properties` arrays.

`document.py` composes extraction with MTC metadata, chemistry indices (IIW carbon equivalent, weldability class, and PREN), and grade-based chemistry checks. ASTM composition ranges are configured for A105 and A182 F316; an unconfigured grade or incomplete composition is returned with warnings and `requires_hitl: true`, rather than being treated as verified. The endpoint retains the existing `native_pdf` extraction label for native-text PDFs.
