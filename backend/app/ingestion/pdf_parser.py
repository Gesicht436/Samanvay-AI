"""
Dual-Path Document Parser for Digital PDFs and Scanned Inspection Certificates.
Fast Path (<50ms): Direct vector stream extraction via pdfplumber.
Slow Path: Image rendering and OCR via PaddleOCR / EasyOCR.
"""

import io
import time
import logging
from typing import Dict, Any, Optional
import pdfplumber
from backend.app.ingestion.certificate import parse_mtc_tables
from backend.app.ingestion.ocr_engine import run_ocr
from backend.app.ml.ner_tagger import extract_attributes

logger = logging.getLogger(__name__)


def process_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Intelligently routes documents between digital extraction and OCR.
    Extracts text, structured key-value tables, and normalized attributes.
    """
    t0 = time.time()
    raw_text = ""
    tables = []
    is_scanned = False

    # Check if input is PDF
    is_pdf = filename.lower().endswith(".pdf") or file_bytes[:4] == b"%PDF"

    if is_pdf:
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    # 1. Digital stream extraction
                    page_text = page.extract_text() or ""
                    raw_text += page_text + "\n"

                    # 2. Extract tables
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)

            # If digital text stream is empty, trigger OCR slow path
            if len(raw_text.strip()) < 30:
                logger.info(f"[+] Document '{filename}' has no selectable text stream. Falling back to OCR.")
                is_scanned = True
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    for page in pdf.pages:
                        pix = page.to_image(resolution=300)
                        img_byte_arr = io.BytesIO()
                        pix.original.save(img_byte_arr, format="PNG")
                        ocr_text = run_ocr(img_byte_arr.getvalue())
                        raw_text += ocr_text + "\n"

        except Exception as e:
            logger.error(f"[-] Error parsing PDF '{filename}': {e}")
            raw_text = run_ocr(file_bytes)
            is_scanned = True

    else:
        # Direct image file (PNG/JPG)
        is_scanned = True
        raw_text = run_ocr(file_bytes)

    duration_ms = (time.time() - t0) * 1000
    logger.info(f"[+] Processed '{filename}' in {duration_ms:.2f}ms (is_scanned={is_scanned})")

    # Parse MTC tabular layout
    parsed_metadata = parse_mtc_tables(tables, raw_text)

    # Document type detection
    doc_type = "MTC_CERTIFICATE"
    upper_text = raw_text.upper()
    if "CHALLAN" in upper_text or "INWARD SLIP" in upper_text or "DELIVERY" in upper_text:
        doc_type = "DELIVERY_CHALLAN"
    elif "FASTENER" in upper_text or "BOLT" in upper_text:
        doc_type = "FASTENER_QUALITY_CERTIFICATE"

    confidence = 0.95 if not is_scanned else 0.80

    return {
        "filename": filename,
        "doc_type": doc_type,
        "raw_text": raw_text.strip(),
        "parsed_metadata": parsed_metadata,
        "confidence": confidence,
        "is_scanned": is_scanned,
        "processing_time_ms": round(duration_ms, 2)
    }
