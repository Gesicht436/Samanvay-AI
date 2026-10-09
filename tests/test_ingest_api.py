import io

import fitz
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_manual_text_returns_shared_ingest_shape():
    response = client.post("/v1/ingest/text", json={"raw_text": "Certificate No: MTC-7"})

    assert response.status_code == 200
    assert response.json() == {
        "filename": None,
        "raw_text": "Certificate No: MTC-7",
        "parsed_metadata": {
            "certificate_type": "MTC",
            "certificate_number": "MTC-7",
            "purchase_order": None,
            "material_grade": None,
            "governing_standard": None,
            "heat_numbers": [],
            "quantity": None,
            "yield_strength_mpa": None,
            "tensile_strength_mpa": None,
            "elongation_pct": None,
            "product_description": None,
            "chemical_composition": [],
            "mechanical_properties": [],
            "manufacturer_list": [],
            "tpi_list": [],
            "engineering_attributes": {
                "item_type": None,
                "size_nb_mm": None,
                "pressure_class": None,
                "metallurgy": None,
                "facing_end": None,
                "standard": None,
                "material_grade": None,
                "indian_standard": None,
                "oisd_standard": None,
                "eil_specification": None,
                "gem_category": None,
                "gem_bid_number": None,
                "cppp_tender_id": None,
                "mesc_code": None,
                "manufacturer": None,
                "product_form": None,
                "coating": None,
                "inspection_class": None,
                "document_number": None,
                "project": None,
                "end_connection": None,
                "temperature_rating": None,
                "purchase_order": None,
                "certificate_number": "MTC-7",
                "bid_number": None,
                "inspection_agency": None,
            },
        },
        "confidence": 1.0,
        "extraction_method": "manual_text",
        "page_count": 1,
    }


def test_document_rejects_unsupported_extension():
    response = client.post("/v1/ingest/document", files={"file": ("notes.txt", b"hello", "text/plain")})

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_document_rejects_uploads_over_15_mb():
    response = client.post("/v1/ingest/document", files={"file": ("large.pdf", io.BytesIO(b"x" * (15 * 1024 * 1024 + 1)), "application/pdf")})

    assert response.status_code == 413


def test_native_pdf_document_returns_shared_ingest_shape():
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Certificate No: MTC-8")
    payload = document.tobytes()
    document.close()

    response = client.post("/v1/ingest/document", files={"file": ("certificate.pdf", payload, "application/pdf")})

    assert response.status_code == 200
    payload = response.json()
    assert payload["extraction_method"] == "native_pdf"
    assert payload["page_count"] == 1
    assert payload["confidence"] == 1.0
    assert payload["pages"][0]["extraction_method"] == "pymupdf"
    assert payload["mtc"]["cert_no"] == "MTC-8"
    assert payload["chemistry"]["carbon_equivalent_iiw"] is None
    assert payload["astm_conformance"]["conforming"] is False
    assert payload["requires_hitl"] is True
    assert payload["ocr_profile"] == {
        "routing": "per_page_hybrid",
        "raster_dpi": 300,
        "preprocessing": ["denoise", "deskew", "contrast"],
        "primary_engine": "paddleocr",
        "fallback_engine": "easyocr",
        "mtc_intelligence": True,
        "chemistry_extraction": True,
    }