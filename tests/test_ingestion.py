import fitz

from OCR.normalization import normalize_text
from OCR.pipeline import extract_document


def test_normalization_maps_nominal_size_and_abbreviations():
    assert normalize_text("FLG WN DN50 RF 300#") == "FLANGE WELD NECK SIZE_NB_MM=50 RAISED FACE CLASS=300"
    assert normalize_text("50 mm") == "SIZE_NB_MM=50"


def test_native_pdf_uses_pymupdf_without_ocr(tmp_path):
    path = tmp_path / "certificate.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Certificate No: MTC-1\nDN50 50 mm")
    document.save(path)
    document.close()

    extraction = extract_document(path)

    assert extraction.extraction_method == "pymupdf"
    assert extraction.source_type == "pdf"
    assert "SIZE_NB_MM=50" in extraction.normalized_text


def test_bytes_pdf_routes_each_page_and_renders_ocr_at_300_dpi(monkeypatch):
    from OCR import pipeline

    document = fitz.open()
    native_page = document.new_page(width=72, height=72)
    native_page.insert_text((5, 15), "Native")
    document.new_page(width=72, height=72)
    payload = document.tobytes()
    document.close()
    raster_sizes = []

    class FakeFallbackEngine:
        def extract(self, image):
            raster_sizes.append(image.shape)
            return "paddleocr", [
                {"text": "Scanned certificate text", "score": 0.99, "box": [0, 0, 1, 1], "x": 0, "y": 0}
            ]

    monkeypatch.setattr(pipeline, "FallbackOCREngine", FakeFallbackEngine)
    monkeypatch.setattr(pipeline, "_preprocess_image", lambda image: image)

    extraction = pipeline.extract_document(payload, "mixed.pdf")

    assert extraction.extraction_method == "hybrid_ocr"
    assert [page["extraction_method"] for page in extraction.pages] == ["pymupdf", "paddleocr"]
    assert extraction.pages[0]["raster_dpi"] is None
    assert extraction.pages[1]["raster_dpi"] == 300
    assert raster_sizes == [(300, 300, 3)]
    assert "Native" in extraction.raw_text
    assert "Scanned certificate text" in extraction.raw_text


def test_bytes_image_opens_without_explicit_filetype(monkeypatch):
    from io import BytesIO

    import numpy as np
    from PIL import Image

    from OCR import pipeline

    image_bytes = BytesIO()
    Image.new("RGB", (30, 20), "white").save(image_bytes, format="PNG")

    class FakeFallbackEngine:
        def extract(self, image):
            return "paddleocr", [
                {"text": "Image content", "score": 0.9, "box": [0, 0, 10, 10], "x": 0, "y": 0}
            ]

    monkeypatch.setattr(pipeline, "FallbackOCREngine", FakeFallbackEngine)
    monkeypatch.setattr(pipeline, "_preprocess_image", lambda image: image)

    extraction = pipeline.extract_document(image_bytes.getvalue(), "photo.png")

    assert extraction.source_type == "image"
    assert extraction.pages[0]["text"] == "Image content"
    assert np.asarray(Image.open(BytesIO(image_bytes.getvalue()))).shape == (20, 30, 3)


def test_pdf_ocr_rejects_invalid_raster_dimensions(monkeypatch):
    import pytest

    from OCR import pipeline

    document = fitz.open()
    document.new_page()
    payload = document.tobytes()
    document.close()
    monkeypatch.setattr(pipeline, "_preprocess_image", lambda image: object())

    with pytest.raises(RuntimeError, match="invalid image dimensions"):
        pipeline.extract_document(payload, "blank.pdf")


def test_reading_order_groups_lines_by_box_overlap_not_fixed_y_buckets():
    from OCR.engine import _reading_order

    blocks = [
        {"text": "right", "x": 100, "y": 10, "box": [100, 10, 150, 24]},
        {"text": "next row", "x": 0, "y": 28, "box": [0, 28, 80, 42]},
        {"text": "left", "x": 0, "y": 3, "box": [0, 3, 50, 17]},
    ]

    ordered = _reading_order(blocks)

    assert [block["text"] for block in ordered] == ["left", "right", "next row"]


def test_skew_estimation_checks_eleven_angles(monkeypatch):
    import numpy as np

    from OCR import pipeline

    checked_angles = []
    original_linspace = pipeline.np.linspace

    def track_angles(*args, **kwargs):
        angles = original_linspace(*args, **kwargs)
        checked_angles.extend(angles.tolist())
        return angles

    monkeypatch.setattr(pipeline.np, "linspace", track_angles)

    image = np.full((40, 60, 3), 255, dtype=np.uint8)
    image[10:15, 10:50] = 0

    pipeline._estimate_skew(image)

    assert len(checked_angles) == 11


def test_ocr_uses_easyocr_when_paddle_fails(monkeypatch):
    from OCR import engine

    class BrokenPaddleEngine:
        def __init__(self):
            raise RuntimeError("Paddle unavailable")

    class FakeEasyEngine:
        def extract(self, image):
            return [{"text": "Recovered text", "score": 0.9, "box": [], "x": 0, "y": 0}]

    monkeypatch.setattr(engine, "PaddleOCREngine", BrokenPaddleEngine)
    monkeypatch.setattr(engine, "EasyOCREngine", FakeEasyEngine)

    selected_engine, blocks = engine.FallbackOCREngine().extract(object())

    assert selected_engine == "easyocr"
    assert blocks[0]["text"] == "Recovered text"


def test_paddle_initialization_failure_is_cached_for_document(monkeypatch):
    from OCR import engine

    initialization_attempts = []

    class BrokenPaddleEngine:
        def __init__(self):
            initialization_attempts.append(1)
            raise RuntimeError("Paddle unavailable")

    class FakeEasyEngine:
        def extract(self, image):
            return [{"text": "Recovered text", "score": 0.9, "box": [], "x": 0, "y": 0}]

    monkeypatch.setattr(engine, "PaddleOCREngine", BrokenPaddleEngine)
    monkeypatch.setattr(engine, "EasyOCREngine", FakeEasyEngine)
    fallback = engine.FallbackOCREngine()

    fallback.extract(object())
    fallback.extract(object())

    assert len(initialization_attempts) == 1


def test_empty_paddle_page_does_not_disable_primary_for_later_pages(monkeypatch):
    from OCR import engine

    class IntermittentPaddleEngine:
        def __init__(self):
            self.calls = 0

        def extract(self, image):
            self.calls += 1
            if self.calls == 1:
                return []
            return [{"text": "Later page", "score": 0.9, "box": [], "x": 0, "y": 0}]

    class FakeEasyEngine:
        def extract(self, image):
            return [{"text": "Fallback page", "score": 0.9, "box": [], "x": 0, "y": 0}]

    paddle = IntermittentPaddleEngine()
    monkeypatch.setattr(engine, "PaddleOCREngine", lambda: paddle)
    monkeypatch.setattr(engine, "EasyOCREngine", FakeEasyEngine)
    fallback = engine.FallbackOCREngine()

    first_engine, _ = fallback.extract(object())
    second_engine, second_blocks = fallback.extract(object())

    assert first_engine == "easyocr"
    assert second_engine == "paddleocr"
    assert second_blocks[0]["text"] == "Later page"


def test_preprocessing_preserves_rgb_shape_and_type():
    import numpy as np

    from OCR.pipeline import _preprocess_image

    image = np.full((40, 60, 3), 255, dtype=np.uint8)
    image[10:13, 5:55] = 0
    image[25:28, 5:50] = 0

    processed = _preprocess_image(image)

    assert processed.shape == image.shape
    assert processed.dtype == np.uint8


def test_certificate_metadata_keeps_each_labelled_line_separate():
    from backend.app.ingestion import clean_text, parse_mtc_certificate

    metadata = parse_mtc_certificate(clean_text("""Certificate No: MTC-9
Material Grade: ASTM A105
Standard: ASME SA-105
Heat No: H-123
Description: Forged flange"""))

    assert metadata["material_grade"] == "ASTM A105"
    assert metadata["governing_standard"] == "ASME SA-105"
    assert metadata["heat_numbers"] == ["H-123"]
    assert metadata["product_description"] == "Forged flange"


def test_manufacturer_and_tpi_lists_include_distinct_document_values():
    from backend.app.ingestion import parse_mtc_certificate

    metadata = parse_mtc_certificate(
        """Manufacturer: Acme Steel
TPI: SGS
Manufacturer: Beta Forge
Inspection Agency: Bureau Veritas"""
    )

    assert metadata["manufacturer_list"] == ["Acme Steel", "Beta Forge"]
    assert metadata["tpi_list"] == ["SGS", "Bureau Veritas"]


def test_certificate_metadata_reads_two_line_pdf_fields():
    from backend.app.ingestion import clean_text, parse_mtc_certificate

    metadata = parse_mtc_certificate(clean_text("""Certificate No:
MTC-2025-FLG-8819
Purchase Order:
PO-IOCL-PNP-77410
Heat / Batch No:
HT-98421-B
Product Description:
WELD NECK FLANGE 4 INCH CLASS 300
Quantity:
45 PCS
Material Specification:
ASTM A105N (NORMALIZED)
Governing Standard:
ASME B16.5 / NACE MR0175
Yield (MPa)
310
Tensile (MPa)
525
Elongation (%)
29.5"""))

    assert metadata["certificate_number"] == "MTC-2025-FLG-8819"
    assert metadata["purchase_order"] == "PO-IOCL-PNP-77410"
    assert metadata["heat_numbers"] == ["HT-98421-B"]
    assert metadata["material_grade"] == "ASTM A105N (NORMALIZED)"
    assert metadata["governing_standard"] == "ASME B16.5 / NACE MR0175"
    assert metadata["quantity"] == "45 PCS"
    assert metadata["yield_strength_mpa"] == 310.0
    assert metadata["tensile_strength_mpa"] == 525.0
    assert metadata["elongation_pct"] == 29.5


def test_certificate_metadata_reads_mechanical_table_values():
    from backend.app.ingestion import parse_mtc_certificate

    metadata = parse_mtc_certificate("""2. MECHANICAL TEST PROPERTIES
Yield (MPa)
Tensile (MPa)
Elongation (%)
Hardness (HBW)
310
525
29.5
156""")

    assert metadata["yield_strength_mpa"] == 310.0
    assert metadata["tensile_strength_mpa"] == 525.0
    assert metadata["elongation_pct"] == 29.5
