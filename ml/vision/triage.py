"""Document triage and classification module for EN 10204 MTC inputs."""

import io
import logging
import fitz  # PyMuPDF
from PIL import Image

from ml.vision.config import DEFAULT_CONFIG, OCRConfig
from ml.vision.exceptions import (
    CorruptFileError,
    EncryptedFileError,
    PageLimitExceededError,
    UnsupportedFormatError,
)

logger = logging.getLogger(__name__)

MAGIC_SIGNATURES = {
    "pdf": b"%PDF",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpeg": b"\xff\xd8\xff",
}


def verify_file_integrity(
    file_bytes: bytes, config: OCRConfig = DEFAULT_CONFIG
) -> str:
    """Validates file non-emptiness, size limit, and magic byte signatures."""
    if not file_bytes or len(file_bytes) == 0:
        raise CorruptFileError("Input file is empty (0 bytes).")

    if len(file_bytes) > config.max_file_size_bytes:
        raise PageLimitExceededError(
            f"File size ({len(file_bytes)} bytes) exceeds maximum limit of {config.max_file_size_bytes} bytes."
        )

    for fmt, magic in MAGIC_SIGNATURES.items():
        if file_bytes.startswith(magic):
            return fmt

    raise UnsupportedFormatError(
        "Unsupported file format. Input bytes do not match PDF, PNG, or JPEG magic headers."
    )


def classify_pdf_page(
    page: fitz.Page, config: OCRConfig = DEFAULT_CONFIG
) -> tuple[str, str]:
    """Classifies a single PDF page as 'digital_vector', 'scanned_raster', or 'garbled'."""
    text = page.get_text("text").strip()
    char_count = len(text)

    if char_count >= config.digital_page_char_limit:
        printable_chars = sum(1 for c in text if c.isprintable() and not c.isspace())
        ratio = printable_chars / float(max(1, char_count))
        if ratio >= config.printable_char_ratio_min:
            return "digital_vector", text
        else:
            return "garbled", text

    return "scanned_raster", text


def inspect_document(
    file_bytes: bytes, config: OCRConfig = DEFAULT_CONFIG
) -> dict:
    """Performs document inspection and returns page classification metadata."""
    fmt = verify_file_integrity(file_bytes, config)

    if fmt in ("png", "jpeg"):
        try:
            img = Image.open(io.BytesIO(file_bytes))
            img.verify()
        except Exception as e:
            raise CorruptFileError(f"Image payload is corrupted: {e}") from e

        return {
            "format": fmt,
            "page_count": 1,
            "pages": [{"page_num": 1, "type": "scanned_raster", "text": ""}],
        }

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise CorruptFileError(f"Failed to parse PDF document stream: {e}") from e

    if doc.is_encrypted:
        doc.close()
        raise EncryptedFileError("PDF document is password protected / encrypted.")

    page_count = len(doc)
    if page_count > config.max_page_limit:
        doc.close()
        raise PageLimitExceededError(
            f"Document has {page_count} pages, exceeding limit of {config.max_page_limit}."
        )

    pages_meta = []
    for page_idx in range(page_count):
        page = doc[page_idx]
        p_type, text = classify_pdf_page(page, config)
        pages_meta.append(
            {"page_num": page_idx + 1, "type": p_type, "text": text}
        )

    doc.close()
    return {"format": "pdf", "page_count": page_count, "pages": pages_meta}
