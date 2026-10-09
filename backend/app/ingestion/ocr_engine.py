from typing import Any


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
