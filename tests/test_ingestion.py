"""
Unit Tests for Multi-Modal Document Intake and Batch Streaming Loader.
Validates extraction against ground-truth MTCs, ERP catalog dumps,
Carbon Equivalent (CE) computation, and image pre-processing transforms.
"""

from pathlib import Path
from PIL import Image
import numpy as np
import pytest
from backend.app.ingestion.pdf_parser import process_document
from backend.app.ingestion.data_pipeline.loader import stream_catalog_batches
from backend.app.ingestion.certificate import (
    compute_carbon_equivalent,
    validate_mechanical_thresholds,
    detect_granular_document_type,
    normalize_mtc_text
)
from backend.app.ingestion.ocr_engine import preprocess_image_for_ocr, estimate_skew_angle

RAW_DIR = Path("data/raw")
CATALOG_CSV = Path("data/mock_cpes_catalogs/iocl_materials.csv")


def test_process_sample_mtc_flange():
    """Test extraction of sample_mtc_flange_01.pdf against expected fields."""
    pdf_path = RAW_DIR / "sample_mtc_flange_01.pdf"
    assert pdf_path.exists(), f"Missing test fixture {pdf_path}"

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    result = process_document(file_bytes, "sample_mtc_flange_01.pdf")

    assert result["filename"] == "sample_mtc_flange_01.pdf"
    assert result["doc_type"] == "MTC_CERTIFICATE"
    assert result["is_scanned"] is False
    assert result["confidence"] >= 0.90

    meta = result["parsed_metadata"]
    assert meta["cert_no"] == "MTC-2025-FLG-8819"
    assert meta["po_no"] == "PO-IOCL-PNP-77410"
    assert meta["heat_no"] == "HT-98421-B"
    assert "WELD NECK" in meta["description"].upper()

    specs = meta["extracted_attributes"]
    assert specs["item_type"] == "FLANGE_WELD_NECK"
    assert specs["size_nb_mm"] == 100.0
    assert specs["pressure_class"] == 300
    assert specs["facing_end"] == "RF"


def test_process_sample_challan_valve():
    """Test extraction of sample_challan_valve_05.pdf."""
    pdf_path = RAW_DIR / "sample_challan_valve_05.pdf"
    assert pdf_path.exists()

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    result = process_document(file_bytes, "sample_challan_valve_05.pdf")

    assert result["doc_type"] == "DELIVERY_CHALLAN"
    meta = result["parsed_metadata"]
    assert meta["cert_no"] == "DC-2025-99014"
    assert meta["heat_no"] == "HT-11983-M"
    assert "BALL VALVE" in meta["description"].upper()

    specs = meta["extracted_attributes"]
    assert specs["item_type"] == "BALL_VALVE"
    assert specs["size_nb_mm"] == 100.0
    assert specs["pressure_class"] == 300


def test_stream_catalog_batches():
    """Test streaming chunk ingestion of CPSE catalog CSV."""
    assert CATALOG_CSV.exists(), f"Missing mock catalog {CATALOG_CSV}"

    batch_count = 0
    total_items = 0
    for batch in stream_catalog_batches(str(CATALOG_CSV), "iocl_materials.csv", batch_size=50):
        batch_count += 1
        total_items += len(batch)
        assert len(batch) <= 50
        first_item = batch[0]
        assert "raw_description" in first_item
        assert "local_code" in first_item
        assert "extracted_attributes" in first_item
        if batch_count >= 3:
            break  # Test first 3 batches for speed

    assert batch_count == 3
    assert total_items == 150


def test_process_real_scanned_procurement_images():
    """Validates native OCR extraction on real procurement images in data/scanned_images."""
    scanned_dir = Path("data/scanned_images")
    if not scanned_dir.exists():
        pytest.skip("Scanned images directory not present")

    # Test Image (1).jpeg - MTC for ASTM A105 Flanges
    img1_path = scanned_dir / "Image (1).jpeg"
    if img1_path.exists():
        with open(img1_path, "rb") as f:
            res1 = process_document(f.read(), "Image (1).jpeg")
        assert res1["is_scanned"] is True
        assert res1["doc_type"] == "MTC_CERTIFICATE"
        meta1 = res1["parsed_metadata"]
        assert meta1["cert_no"] == "MTC20201289"
        assert meta1["material_grade"] == "ASTM A105"
        assert len(meta1["extracted_items"]) >= 5
        assert meta1["nace_compliant"] is True
        assert meta1["manufacturer"] == "MAG GENERAL BUSINESS"
        assert "C" in meta1["chemical_dict"]
        assert "tensile" in meta1["mechanical_dict"]

    # Test Image (4).jpeg - MTC for ASTM A105 Weld Neck Flanges
    img4_path = scanned_dir / "Image (4).jpeg"
    if img4_path.exists():
        with open(img4_path, "rb") as f:
            res4 = process_document(f.read(), "Image (4).jpeg")
        assert res4["is_scanned"] is True
        meta4 = res4["parsed_metadata"]
        assert meta4["cert_no"] == "B339004F1"
        assert meta4["material_grade"] == "ASTM A105"
        assert len(meta4["extracted_items"]) >= 2


def test_carbon_equivalent_computation():
    """Validates Carbon Equivalent (CE) formula and weldability status."""
    # Standard ASTM A105 Chemistry: C=0.20%, Mn=0.80%, Si=0.25%, Cr=0.10%, Mo=0.04%, V=0.02%, Ni=0.15%, Cu=0.15%
    # CE = 0.20 + (0.80 / 6) + (0.16 / 5) + (0.30 / 15) = 0.20 + 0.133 + 0.032 + 0.02 = 0.385%
    chem_good = {
        "C": "0.20%", "Mn": "0.80%", "Si": "0.25%",
        "Cr": "0.10%", "Mo": "0.04%", "V": "0.02%",
        "Ni": "0.15%", "Cu": "0.15%"
    }
    ce_res = compute_carbon_equivalent(chem_good)
    assert ce_res is not None
    assert 0.37 <= ce_res["carbon_equivalent"] <= 0.40
    assert ce_res["is_standard_weldable"] is True
    assert ce_res["status"] in ["EXCELLENT_WELDABILITY", "ACCEPTABLE_WELDABILITY"]

    # High Carbon steel with elevated CE (>0.43%)
    chem_high = {
        "C": "0.28%", "Mn": "1.20%", "Si": "0.35%",
        "Cr": "0.20%", "Mo": "0.10%", "V": "0.05%",
        "Ni": "0.25%", "Cu": "0.20%"
    }
    ce_high_res = compute_carbon_equivalent(chem_high)
    assert ce_high_res is not None
    assert ce_high_res["carbon_equivalent"] > 0.43
    assert ce_high_res["is_standard_weldable"] is False
    assert ce_high_res["status"] == "PREHEAT_REQUIRED_HIGH_CE"


def test_mechanical_threshold_validation():
    """Validates ASTM strength warnings for below-standard mechanical properties."""
    # Defective A105 sample with weak yield strength (220 MPa < 250 MPa minimum)
    mech_weak = {"yield": "220 MPa", "tensile": "510 MPa"}
    warnings = validate_mechanical_thresholds("ASTM A105", mech_weak)
    assert len(warnings) >= 1
    assert "Yield Strength" in warnings[0]

    # Compliant A105 sample
    mech_compliant = {"yield": "310 MPa", "tensile": "540 MPa"}
    warnings_comp = validate_mechanical_thresholds("ASTM A105", mech_compliant)
    assert len(warnings_comp) == 0


def test_image_preprocessing_pipeline():
    """Validates deskew estimation and image enhancement transforms."""
    # Create synthetic test image with text-like pattern
    img = Image.new("RGB", (800, 600), color=(240, 240, 240))
    enhanced = preprocess_image_for_ocr(
        img,
        apply_deskew=True,
        apply_contrast=True,
        apply_binarization=False
    )
    assert enhanced.size[0] >= 1600  # Resolution normalized
    assert enhanced.mode == "L"       # Converted to grayscale


def test_granular_document_subclassification():
    """Validates granular document type and subtype detection."""
    challan_text = "MATERIAL DISPATCH DELIVERY CHALLAN IOCL PANIPAT TO ONGC HAZIRA"
    doc_t, doc_sub = detect_granular_document_type(challan_text)
    assert doc_t == "DELIVERY_CHALLAN"
    assert doc_sub == "DELIVERY_CHALLAN_CPSE"

    tpi_mtc_text = "EN 10204 3.2 INSPECTION CERTIFICATE TPI WITNESSED BY LLOYDS REGISTER"
    doc_t2, doc_sub2 = detect_granular_document_type(tpi_mtc_text)
    assert doc_t2 == "MTC_CERTIFICATE"
    assert doc_sub2 == "MTC_EN10204_3_2"
