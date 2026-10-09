from pathlib import Path


def _text_density(text: str, page_area: float) -> float:
    if page_area <= 0:
        return 0.0
    return len("".join(text.split())) / page_area


def extract_pdf_text(path: str | Path, density_threshold: float = 0.0005) -> str:
    """Extract text directly when possible, otherwise route pages through OCR."""
    import fitz

    with fitz.open(path) as document:
        pages: list[str] = []
        needs_ocr = False
        for page in document:
            text = page.get_text("text")
            area = page.rect.width * page.rect.height
            if not text.strip() or _text_density(text, area) < density_threshold:
                needs_ocr = True
            pages.append(text)
        if not needs_ocr:
            return "\n\n".join(" ".join(page.split()) for page in pages).strip()

        from .ocr_engine import extract_ocr_text

        return extract_ocr_text(document)
