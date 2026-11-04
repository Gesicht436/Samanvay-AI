"""OCR engine integration for both scanned documents and vector PDFs."""

from pathlib import Path
from typing import Any, Dict


def extract_ocr_text(document: Any) -> str:
    """Run orientation-aware OCR and reconstruct lines by bounding-box position."""
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError("Install the optional 'ml' dependencies to process scanned PDFs") from exc

    engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    lines: list[tuple[float, float, str]] = []
    for page in document:
        image = page.get_pixmap(matrix=None, alpha=False).pil_image()
        result = engine.ocr(image, cls=True)
        for block in result or []:
            for box, value in block or []:
                text, score = value
                if score < 0.4:
                    continue
                x = min(point[0] for point in box)
                y = min(point[1] for point in box)
                lines.append((y, x, text))
    lines.sort(key=lambda item: (round(item[0] / 8), item[1]))
    return "\n".join(text for _, _, text in lines)


class OCREngine:
    """
    Dual-path document text extraction engine supporting both vector PDFs and scanned raster sheets.
    Wraps the optimized OCR pipeline from the OCR package.
    """

    def __init__(self) -> None:
        pass

    def classify_document(self, doc_bytes: bytes, filename: str) -> str:
        """
        Classifies whether a document is a digital vector PDF or requires raster OCR.
        """
        suffix = Path(filename).suffix.lower()
        if suffix == ".pdf":
            try:
                import fitz

                doc = fitz.open(stream=doc_bytes, filetype="pdf")
                total_text_len = 0
                for page in doc:
                    total_text_len += len(page.get_text().strip())
                doc.close()
                if total_text_len > 40:
                    return "digital_vector"
            except Exception:
                pass
        return "raster_scan"

    def extract_document(self, doc_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Extracts document text using fast vector PyMuPDF or multi-engine OCR fallback.
        """
        from OCR.pipeline import extract_document as _extract_doc

        extraction = _extract_doc(doc_bytes, filename)
        is_vector = extraction.extraction_method == "pymupdf"
        return {
            "doc_type": "DIGITAL_VECTOR_PDF" if is_vector else "RASTER_IMAGE_OCR",
            "is_scanned": not is_vector,
            "confidence_score": 1.0 if is_vector else extraction.confidence,
            "raw_text": extraction.raw_text,
            "pages": extraction.pages,
        }

    def preprocess_image(self, image: Any) -> Any:
        """
        Normalizes image dimensions and enhances contrast for OCR readability.
        """
        from PIL import Image

        w, h = image.size
        min_dim = min(w, h)
        if min_dim < 1600:
            scale = 1600.0 / min_dim
            new_w, new_h = int(w * scale), int(h * scale)
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return image
