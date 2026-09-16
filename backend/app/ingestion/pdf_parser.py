"""
Dual-Path Document Parser for Digital PDFs and Scanned Inspection Certificates.
Fast Path (<50ms): Direct vector stream extraction via pdfplumber.
Slow Path: Parallel multi-page image rendering and OCR via WinOCR / PaddleOCR / EasyOCR.
"""

import io
import time
import logging
import concurrent.futures
from typing import Dict, Any, List, Optional
import pdfplumber
from backend.app.ingestion.certificate import parse_mtc_tables, detect_granular_document_type
from backend.app.ingestion.ocr_engine import run_ocr
from backend.app.ml.ner_tagger import extract_attributes

logger = logging.getLogger(__name__)

_page_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def _ocr_pdf_page(page_data: Tuple[int, Any]) -> Tuple[int, str]:
    """Helper to render and OCR a single PDF page in a worker thread."""
    page_idx, page = page_data
    try:
        pix = page.to_image(resolution=300)
        img_byte_arr = io.BytesIO()
        pix.original.save(img_byte_arr, format="PNG")
        text = run_ocr(img_byte_arr.getvalue())
        return page_idx, text
    except Exception as e:
        logger.error(f"[-] Error running OCR on page {page_idx}: {e}")
        return page_idx, ""


def process_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Intelligently routes documents between digital extraction and OCR.
    Handles multi-page parallel processing, structured key-value tables,
    chemical/mechanical validation, and multi-item line extractions.
    """
    t0 = time.time()
    raw_text = ""
    tables: List[List[List[Optional[str]]]] = []
    is_scanned = False
    page_count = 1

    # Check if input is PDF
    is_pdf = filename.lower().endswith(".pdf") or file_bytes[:4] == b"%PDF"

    if is_pdf:
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    # 1. Digital stream extraction
                    page_text = page.extract_text() or ""
                    raw_text += page_text + "\n"

                    # 2. Extract tables
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)

            # If digital text stream is empty or minimal, trigger parallel OCR slow path
            if len(raw_text.strip()) < 35:
                logger.info(f"[+] Document '{filename}' has no selectable text stream. Executing parallel OCR across {page_count} pages.")
                is_scanned = True
                raw_text = ""

                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    pages_to_process = [(idx, page) for idx, page in enumerate(pdf.pages)]
                    
                    if len(pages_to_process) == 1:
                        _, text = _ocr_pdf_page(pages_to_process[0])
                        raw_text = text
                    else:
                        # Multi-page parallel processing
                        futures = [_page_thread_pool.submit(_ocr_pdf_page, p_data) for p_data in pages_to_process]
                        results = [f.result(timeout=45.0) for f in futures]
                        # Sort by original page index
                        results.sort(key=lambda x: x[0])
                        raw_text = "\n".join([r[1] for r in results])

        except Exception as e:
            logger.error(f"[-] Error parsing PDF '{filename}': {e}")
            raw_text = run_ocr(file_bytes)
            is_scanned = True

    else:
        # Direct image file (PNG/JPG/JPEG/TIFF)
        is_scanned = True
        raw_text = run_ocr(file_bytes)

    duration_ms = (time.time() - t0) * 1000
    logger.info(f"[+] Processed '{filename}' in {duration_ms:.2f}ms (is_scanned={is_scanned}, pages={page_count})")

    # Parse MTC tabular layout and metadata
    parsed_metadata = parse_mtc_tables(tables, raw_text)
    doc_type = parsed_metadata.get("doc_subtype") or "MTC_CERTIFICATE"
    
    # Standard top-level doc_type for backward compatibility with existing tests
    top_doc_type = "MTC_CERTIFICATE"
    upper_text = raw_text.upper()
    if "CHALLAN" in upper_text or "INWARD SLIP" in upper_text or "DELIVERY" in upper_text:
        top_doc_type = "DELIVERY_CHALLAN"
    elif "FASTENER" in upper_text or "BOLT" in upper_text:
        top_doc_type = "FASTENER_QUALITY_CERTIFICATE"

    confidence = 0.95 if not is_scanned else 0.85

    return {
        "filename": filename,
        "doc_type": top_doc_type,
        "doc_subtype": parsed_metadata.get("doc_subtype", top_doc_type),
        "raw_text": raw_text.strip(),
        "parsed_metadata": parsed_metadata,
        "confidence": confidence,
        "is_scanned": is_scanned,
        "page_count": page_count,
        "processing_time_ms": round(duration_ms, 2)
    }
