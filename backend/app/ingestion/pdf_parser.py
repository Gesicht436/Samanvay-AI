import fitz  # PyMuPDF
from typing import Dict, Any, List
from .ocr_engine import run_ocr
from .certificate import parse_mtc_certificate
from .normalizer import clean_text

DIGITAL_TEXT_CHAR_THRESHOLD = 30

def process_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    lower_name = filename.lower()

    if lower_name.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp")):
        raw_ocr_text, confidence = run_ocr(file_bytes)
        cleaned = clean_text(raw_ocr_text)
        metadata = parse_mtc_certificate(cleaned)
        return {
            "filename": filename,
            "raw_text": cleaned,
            "parsed_metadata": metadata,
            "confidence": confidence,
            "extraction_method": "ocr_image",
            "page_count": 1
        }

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    total_pages = len(doc)
    extracted_page_texts: List[str] = []
    page_confidences: List[float] = []
    used_ocr = False

    for page_idx in range(total_pages):
        page = doc[page_idx]
        native_text = page.get_text("text").strip()

        if len(native_text) >= DIGITAL_TEXT_CHAR_THRESHOLD:
            extracted_page_texts.append(native_text)
            page_confidences.append(1.0)
        else:
            used_ocr = True
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            ocr_text, conf = run_ocr(img_bytes)
            extracted_page_texts.append(ocr_text)
            page_confidences.append(conf)

    doc.close()

    raw_combined = "\n\n".join(extracted_page_texts)
    normalized_text = clean_text(raw_combined)
    parsed_metadata = parse_mtc_certificate(normalized_text)

    mean_conf = round(sum(page_confidences) / len(page_confidences), 4) if page_confidences else 0.0

    return {
        "filename": filename,
        "raw_text": normalized_text,
        "parsed_metadata": parsed_metadata,
        "confidence": mean_conf,
        "extraction_method": "hybrid_ocr" if used_ocr else "native_pdf",
        "page_count": total_pages,
    }