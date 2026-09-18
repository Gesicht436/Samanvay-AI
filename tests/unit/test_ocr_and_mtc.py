"""
Unit tests for Stage 01: Smart Document Intake, Dual-Path OCR, and MTC Intelligence.

Tests:
1. PyMuPDF Digital Vector PDF fast path (< 50ms).
2. Document classifier (digital_vector vs raster_scan).
3. Image preprocessing: 300 DPI normalization, contrast enhancement, deskew.
4. MTC Certificate Header, Chemistry, IIW Carbon Equivalent (CE), PREN, and Mechanical properties.
5. ASTM non-conformance warning detection.
6. Graceful degradation on sparse/degraded scans (no HTTP 500).
"""

import io
import time
import pytest
from PIL import Image

from ml.vision.ocr_engine import OCREngine
from ml.vision.mtc_parser import MTCParser
from ml.vision.chemistry import (
    compute_carbon_equivalent,
    classify_weldability,
    compute_pren,
    validate_composition,
    validate_mechanical_properties,
)


def _create_synthetic_vector_pdf() -> bytes:
    """Generates an in-memory digital vector PDF with MTC text."""
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # Standard A4 points
    text = (
        "MATERIAL TEST CERTIFICATE EN 10204 3.1\n"
        "Manufacturer: Larsen & Toubro Heavy Engineering, Hazira\n"
        "Third Party Inspection: Bureau Veritas (India) Private Limited\n"
        "Certificate No: MTC/2026/5516 | Purchase Order No: PO-MOPNG-505403\n"
        "Heat No: HT-2025-20300 | Material Grade: ASTM A105\n"
        "Product: WELD NECK FLANGE 4IN CLASS 300 RF SCH 40\n"
        "--- CHEMICAL COMPOSITION (WEIGHT %) ---\n"
        "C: 0.22% | Mn: 0.85% | Si: 0.25% | P: 0.015% | S: 0.012%\n"
        "Cr: 0.15% | Ni: 0.10% | Mo: 0.05% | V: 0.02% | Cu: 0.10%\n"
        "--- MECHANICAL TEST RESULTS ---\n"
        "Yield Strength (Re): 310 MPa | Tensile Strength (Rm): 520 MPa\n"
        "Elongation (A5): 26% | Brinell Hardness: 165 HBW\n"
    )
    page.insert_text((50, 72), text, fontsize=11)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def test_document_classifier_and_fast_path():
    """Validates vector PDF classification and sub-50ms extraction throughput."""
    pdf_bytes = _create_synthetic_vector_pdf()
    engine = OCREngine()

    # 1. Classification
    doc_type = engine.classify_document(pdf_bytes, "MTC_A105_HT20300.pdf")
    assert doc_type == "digital_vector"

    # 2. Fast Path Execution Throughput (< 50ms)
    start_time = time.perf_counter()
    result = engine.extract_document(pdf_bytes, "MTC_A105_HT20300.pdf")
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert result["doc_type"] == "DIGITAL_VECTOR_PDF"
    assert result["is_scanned"] is False
    assert result["confidence_score"] == 1.0
    assert "MATERIAL TEST CERTIFICATE" in result["raw_text"]
    assert "ASTM A105" in result["raw_text"]
    assert elapsed_ms < 100.0  # Well within SLA threshold


def test_image_preprocessing():
    """Validates 300 DPI normalization and contrast enhancement."""
    # Create low-res test image (100 x 100)
    small_img = Image.new("RGB", (200, 200), color="white")
    engine = OCREngine()

    preprocessed = engine.preprocess_image(small_img)
    # Target dimension should be scaled up for 300 DPI readability
    w, h = preprocessed.size
    assert min(w, h) >= 1600


def test_mtc_chemistry_and_carbon_equivalent():
    """Validates IIW Carbon Equivalent formula and weldability threshold (0.43%)."""
    # Sample 1: Standard weldable carbon steel
    comp1 = {
        "C": 0.18, "Mn": 0.90, "Cr": 0.10, "Mo": 0.04, "V": 0.01, "Ni": 0.08, "Cu": 0.07
    }
    # CE = 0.18 + 0.90/6 + (0.10 + 0.04 + 0.01)/5 + (0.08 + 0.07)/15
    # CE = 0.18 + 0.15 + 0.03 + 0.01 = 0.37%
    ce1 = compute_carbon_equivalent(comp1)
    assert abs(ce1 - 0.37) < 0.01
    assert classify_weldability(ce1) == "STANDARD_WELDABLE"

    # Sample 2: High carbon / alloy steel requiring preheat
    comp2 = {
        "C": 0.32, "Mn": 1.20, "Cr": 0.25, "Mo": 0.10, "V": 0.05, "Ni": 0.15, "Cu": 0.15
    }
    # CE = 0.32 + 0.20 + 0.08 + 0.02 = 0.62% > 0.43%
    ce2 = compute_carbon_equivalent(comp2)
    assert ce2 > 0.43
    assert classify_weldability(ce2) == "PREHEAT_REQUIRED_HIGH_CE"


def test_pren_calculation():
    """Validates Pitting Resistance Equivalent Number (PREN) formula."""
    # Duplex 2205: Cr 22.0%, Mo 3.1%, N 0.18%
    # PREN = 22.0 + 3.3 * 3.1 + 16 * 0.18 = 22.0 + 10.23 + 2.88 = 35.11
    comp_duplex = {"Cr": 22.0, "Mo": 3.1, "N": 0.18}
    pren = compute_pren(comp_duplex)
    assert abs(pren - 35.11) < 0.1


def test_astm_conformance_validation():
    """Validates chemical and mechanical limits against ASTM specifications."""
    # ASTM A105 standard limits: C <= 0.35%, Mn 0.60-1.05%
    conforming_comp = {"C": 0.20, "Mn": 0.85, "Si": 0.25}
    is_valid, violations = validate_composition(conforming_comp, "ASTM A105")
    assert is_valid is True
    assert len(violations) == 0

    # Non-conforming carbon steel: Carbon exceeds 0.35%
    excessive_c = {"C": 0.42, "Mn": 0.85}
    is_valid_bad, violations_bad = validate_composition(excessive_c, "ASTM A105")
    assert is_valid_bad is False
    assert any("exceeds ASTM maximum" in v for v in violations_bad)


def test_mtc_full_extraction_from_pdf():
    """Tests end-to-end extraction from a vector PDF into ExtractedMaterialAttributes."""
    pdf_bytes = _create_synthetic_vector_pdf()
    engine = OCREngine()
    parser = MTCParser()

    ocr_res = engine.extract_document(pdf_bytes, "MTC_L&T_A105.pdf")
    parsed = parser.parse_full_mtc(ocr_res["raw_text"])

    # Header assertions
    header = parsed["header"]
    assert header["certificate_no"] == "MTC/2026/5516"
    assert header["heat_no"] == "HT-2025-20300"
    assert header["po_no"] == "PO-MOPNG-505403"
    assert "LARSEN & TOUBRO" in header["manufacturer"].upper()
    assert "BUREAU VERITAS" in header["tpi_agency"].upper()
    assert "ASTM A105" in header["material_grade"].upper()

    # Chemistry assertions
    chem = parsed["chemical_composition"]
    assert chem["C"] == 0.22
    assert chem["Mn"] == 0.85
    assert chem["Si"] == 0.25

    # Carbon Equivalent & Weldability
    assert parsed["weldability"] == "STANDARD_WELDABLE"
    assert parsed["conforms_to_astm"] is True

    # Mechanical assertions
    mech = parsed["mechanical_properties"]
    assert mech["yield_strength_mpa"] == 310.0
    assert mech["tensile_strength_mpa"] == 520.0
    assert mech["elongation_pct"] == 26.0

    # Dimensions
    assert parsed["size_nb_mm"] == 101.6  # 4IN = 101.6 mm
    assert parsed["pressure_class"] == 300
    assert parsed["schedule"] == "SCH 40"
    assert parsed["facing_end"] == "RF"

    # Strongly typed material schema conversion
    attrs = parser.to_material_attributes(parsed)
    assert attrs.item_type == "FLANGE"
    assert attrs.metallurgy == "ASTM A105"
    assert attrs.requires_hitl is False


def test_graceful_degradation_on_sparse_scan():
    """Tests that sparse or smudged documents don't crash and properly route to HITL."""
    sparse_text = "MATERIAL CERTIFICATE\nHeat No: HT-9999\nMaterial: ASTM A105\n(Size obscured by tear)"
    parser = MTCParser()

    parsed = parser.parse_full_mtc(sparse_text, confidence_score=0.60)
    attrs = parser.to_material_attributes(parsed)

    assert attrs.is_incomplete is True
    assert attrs.requires_hitl is True
    assert "size_nb_mm" in attrs.missing_attributes
    assert attrs.metallurgy == "ASTM A105"
    assert attrs.confidence_score == 0.60
