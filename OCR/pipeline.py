"""Fast native-PDF extraction and PaddleOCR fallback for document ingestion."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fitz
import numpy as np

from .engine import FallbackOCREngine
from .layout import LayoutAnalyzer
from .normalization import normalize_text

RASTER_DPI = 300
OCR_ROUTING = "per_page_hybrid"
OCR_PREPROCESSING = ("denoise", "deskew", "contrast")


@dataclass
class DocumentExtraction:
    raw_text: str
    normalized_text: str
    extraction_method: str
    source_type: str
    pages: list[dict[str, Any]] = field(default_factory=list)
    layout_model: str | None = None

    @property
    def confidence(self) -> float:
        scores = [
            float(block.get("score", 1.0))
            for page in self.pages
            for block in page.get("blocks", [])
            if block.get("score") is not None
        ]
        return sum(scores) / len(scores) if scores else 0.0


def _image_from_page(page: Any) -> Any:
    scale = RASTER_DPI / 72
    pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    return np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, 3)


def _estimate_skew(image: Any) -> float:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Install the optional 'ml' dependencies to preprocess scanned pages") from exc

    grayscale = Image.fromarray(image).convert("L")
    grayscale.thumbnail((1000, 1000))
    pixels = np.asarray(grayscale)
    if not np.any(pixels < 180):
        return 0.0
    angles = np.linspace(-5.0, 5.0, 11)
    best_angle = 0.0
    best_score = -1.0
    for angle in angles:
        rotated = grayscale.rotate(float(angle), resample=Image.Resampling.NEAREST, fillcolor=255)
        row_ink = np.count_nonzero(np.asarray(rotated) < 180, axis=1)
        score = float(np.var(row_ink))
        if score > best_score:
            best_score = score
            best_angle = float(angle)
    return best_angle


def _preprocess_image(image: Any) -> Any:
    try:
        from PIL import Image, ImageFilter, ImageOps
    except ImportError as exc:
        raise RuntimeError("Install the optional 'ml' dependencies to preprocess scanned pages") from exc

    denoised = Image.fromarray(image).filter(ImageFilter.MedianFilter(size=3))
    deskewed = denoised.rotate(
        _estimate_skew(np.asarray(denoised)),
        resample=Image.Resampling.BICUBIC,
        expand=False,
        fillcolor=(255, 255, 255),
    )
    contrasted = ImageOps.autocontrast(deskewed.convert("L"))
    return np.asarray(contrasted.convert("RGB"))


def _extract_document(document: Any, source_type: str) -> DocumentExtraction:
    pages: list[dict[str, Any]] = []
    engine: FallbackOCREngine | None = None
    used_ocr = False
    used_engines: set[str] = set()

    for page_number, page in enumerate(document, start=1):
        text = page.get_text("text")
        words = page.get_text("words")
        if words:
            blocks = [
                {"text": word[4], "score": 1.0, "box": word[:4], "x": word[0], "y": word[1]}
                for word in words
            ]
            page_engine = None
            page_method = "pymupdf"
            raster_dpi = None
        else:
            if engine is None:
                engine = FallbackOCREngine()
            image = _preprocess_image(_image_from_page(page))
            image_shape = getattr(image, "shape", ())
            if (
                len(image_shape) < 2
                or image_shape[0] <= 0
                or image_shape[1] <= 0
            ):
                raise RuntimeError("Rasterized OCR page has invalid image dimensions.")
            page_engine, blocks = engine.extract(image)
            text = "\n".join(block["text"] for block in blocks)
            used_ocr = True
            used_engines.add(page_engine)
            page_method = page_engine
            raster_dpi = RASTER_DPI

        pages.append(
            {
                "page": page_number,
                "text": text,
                "blocks": blocks,
                "height": page.rect.height if page_method == "pymupdf" else int(image_shape[0]),
                "regions": [],
                "extraction_method": page_method,
                "ocr_engine": page_engine,
                "raster_dpi": raster_dpi,
            }
        )

    if used_ocr:
        extraction_method = (
            "hybrid_ocr"
            if source_type == "pdf" or len(used_engines) > 1
            else next(iter(used_engines))
        )
    else:
        extraction_method = "pymupdf"
    raw_text = "\n\n".join(page["text"].strip() for page in pages if page["text"].strip()).strip()
    analyzer = LayoutAnalyzer()
    for page in pages:
        page["regions"] = [
            region.__dict__ for region in analyzer.analyze(page["blocks"], page["height"])
        ]
    return DocumentExtraction(
        raw_text,
        normalize_text(raw_text),
        extraction_method,
        source_type,
        pages,
    )


def extract_document(source: bytes | str | Path, filename: str | None = None) -> DocumentExtraction:
    """Extract a document directly from bytes or from a filesystem path."""
    if isinstance(source, bytes):
        if not filename:
            raise ValueError("A filename is required when extracting document bytes.")
        suffix = Path(filename).suffix.lower()
        if suffix not in {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}:
            raise ValueError("Unsupported document type.")
        source_type = "pdf" if suffix == ".pdf" else "image"
        document = (
            fitz.open(stream=source, filetype="pdf")
            if source_type == "pdf"
            else fitz.open(stream=source)
        )
    else:
        path = Path(source)
        suffix = path.suffix.lower()
        if suffix not in {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}:
            raise ValueError("Unsupported document type.")
        source_type = "pdf" if suffix == ".pdf" else "image"
        document = fitz.open(path)

    with document:
        return _extract_document(document, source_type)