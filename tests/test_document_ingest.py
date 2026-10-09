from io import BytesIO

import fitz
import pytest
from PIL import Image

from backend.app.ingestion.document import ingest_document
from OCR import pipeline

_MTC_TEXT = """Certificate No: MTC-101
Purchase Order: PO-101
Material Grade: ASTM A182 F316
Governing Standard: ASTM A182
Heat No: H-101
Chemical Composition (%)
C Mn Si P S Cr Ni Mo N
0.04 1.20 0.50 0.03 0.02 17.00 12.00 2.50 0.05
Mechanical Properties
Yield Strength (MPa): 310
Tensile Strength (MPa): 525
Elongation (%): 29.5
"""


def _pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((50, 50), text)
    payload = document.tobytes()
    document.close()
    return payload


def test_native_mtc_populates_contract_chemistry_and_astm_conformance():
    response = ingest_document(_pdf_bytes(_MTC_TEXT), "certificate.pdf")

    assert response.extraction_method == "pymupdf"
    assert response.confidence == 1.0
    assert response.ocr_profile.mtc_intelligence
    assert response.ocr_profile.chemistry_extraction
    assert response.mtc is not None
    assert response.mtc.material_grade == "ASTM A182 F316"
    assert response.chemistry["carbon_equivalent_iiw"] is not None
    assert response.chemistry["pren"] is not None
    assert response.astm_conformance["conforming"] is True
    assert response.requires_hitl is False
    assert response.pages[0].raster_dpi is None


def test_scanned_image_uses_ocr_and_calculates_chemistry(monkeypatch):
    class FakeOCREngine:
        def extract(self, image):
            assert len(image.shape) == 3
            assert image.shape[0] > 0 and image.shape[1] > 0
            return "paddleocr", [
                {
                    "text": _MTC_TEXT,
                    "score": 0.91,
                    "box": [0, 0, 20, 20],
                    "x": 0,
                    "y": 0,
                }
            ]

    image_buffer = BytesIO()
    Image.new("RGB", (30, 20), "white").save(image_buffer, format="PNG")
    monkeypatch.setattr(pipeline, "FallbackOCREngine", FakeOCREngine)
    monkeypatch.setattr(pipeline, "_preprocess_image", lambda image: image)

    response = ingest_document(image_buffer.getvalue(), "scan.png")

    assert response.extraction_method == "paddleocr"
    assert response.confidence == 0.91
    assert response.chemistry["carbon_equivalent_iiw"] is not None
    assert response.mtc is not None
    assert response.pages[0].ocr_engine == "paddleocr"
    assert response.pages[0].raster_dpi == 300


def test_non_mtc_document_degrades_to_ocr_text_and_hitl():
    response = ingest_document(
        _pdf_bytes("Purchase Order: PO-55\nDeliver ten industrial valves."),
        "purchase-order.pdf",
    )

    assert "Purchase Order" in response.raw_text
    assert response.mtc is None
    assert response.requires_hitl is True
    assert response.astm_conformance["conforming"] is False
    assert response.chemistry["carbon_equivalent_iiw"] is None


def test_normalized_size_class_and_empty_description_are_supported():
    from backend.app.contracts.matching import ExtractedMaterialAttributes
    from machine_learning.ner_tagger import extract_attributes

    attributes = extract_attributes("SIZE_NB_MM=50 SIZE_IN=4 CLASS=150")

    assert attributes.size_nb_mm == 50
    assert attributes.pressure_class == 150
    assert ExtractedMaterialAttributes().raw_description == ""

    inch_attributes = extract_attributes("SIZE_IN=4")
    assert inch_attributes.size_nb_mm == 101.6


def test_ocr_failure_is_raised_with_original_message(monkeypatch):
    from backend.app.ingestion import document as ingest_module

    def raise_ocr_error(file_bytes, filename):
        raise RuntimeError("OCR engines unavailable")

    monkeypatch.setattr(ingest_module, "extract_document", raise_ocr_error)

    with pytest.raises(RuntimeError, match="OCR engines unavailable"):
        ingest_module.ingest_document(b"not-a-pdf", "document.pdf")


def test_mtc_parser_failure_returns_text_and_requires_hitl(monkeypatch, caplog):
    from backend.app.ingestion import document as ingest_module

    def raise_parser_error(raw_text):
        raise ValueError("invalid MTC layout")

    monkeypatch.setattr(ingest_module, "parse_mtc", raise_parser_error)

    with caplog.at_level("WARNING"):
        response = ingest_module.ingest_document(_pdf_bytes(_MTC_TEXT), "certificate.pdf")

    assert response.raw_text
    assert response.mtc is None
    assert response.requires_hitl is True
    assert "invalid MTC layout" in caplog.text
