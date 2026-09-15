"""
Unit Tests for Machine Learning Attribute Extraction and Feature Normalization.
Tests cross-dialect normalization across IOCL, ONGC, and BPCL procurement strings.
"""

import pytest
from backend.app.ml.ner_tagger import extract_attributes
from backend.app.contracts.material import ItemType, FacingEnd


def test_extract_iocl_dialect():
    """IOCL Dialect: Truncated, imperial units, hashes for class."""
    text = "FLG WNRF 4IN 300# A105"
    attrs = extract_attributes(text)

    assert attrs.item_type == ItemType.FLANGE_WELD_NECK.value
    assert attrs.size_nb_mm == 100.0
    assert attrs.pressure_class == 300
    assert attrs.metallurgy == "ASTM A105"
    assert attrs.facing_end == FacingEnd.RF.value
    assert attrs.extraction_confidence >= 0.8


def test_extract_ongc_dialect():
    """ONGC Dialect: Verbose, comma-delimited, formal naming."""
    text = "FLANGE, WELDING NECK, 4 INCH, CLASS 300, ASTM A105, ASME B16.5, RF FACING"
    attrs = extract_attributes(text)

    assert attrs.item_type == ItemType.FLANGE_WELD_NECK.value
    assert attrs.size_nb_mm == 100.0
    assert attrs.pressure_class == 300
    assert attrs.metallurgy == "ASTM A105"
    assert attrs.facing_end == FacingEnd.RF.value
    assert attrs.standard == "ASME B16.5"
    assert attrs.extraction_confidence == 1.0


def test_extract_bpcl_dialect():
    """BPCL Dialect: Metric-preferred, hyphenated, PN pressure codes."""
    text = "FLG-WN-DN100-PN50-A105-RF"
    attrs = extract_attributes(text)

    assert attrs.item_type == ItemType.FLANGE_WELD_NECK.value
    assert attrs.size_nb_mm == 100.0
    assert attrs.pressure_class == 300  # PN50 maps to ASME Class 300
    assert attrs.metallurgy == "ASTM A105"
    assert attrs.facing_end == FacingEnd.RF.value


def test_extract_valve_wcb():
    """Gate valve extraction with WCB cast carbon steel."""
    text = "VLV GT 2IN 150LB WCB RF"
    attrs = extract_attributes(text)

    assert attrs.item_type == ItemType.GATE_VALVE.value
    assert attrs.size_nb_mm == 50.0
    assert attrs.pressure_class == 150
    assert attrs.metallurgy == "ASTM A216 WCB"
    assert attrs.facing_end == FacingEnd.RF.value


def test_extract_cryogenic_blind_flange_rtj():
    """Cryogenic LF2 blind flange with RTJ facing."""
    text = "FLG BLD RTJ 1.5IN CL900 A350-LF2"
    attrs = extract_attributes(text)

    assert attrs.item_type == ItemType.FLANGE_BLIND.value
    assert attrs.size_nb_mm == 40.0
    assert attrs.pressure_class == 900
    assert attrs.metallurgy == "ASTM A350 LF2"
    assert attrs.facing_end == FacingEnd.RTJ.value


def test_cross_dialect_attribute_parity():
    """Verifies that identical physical items across all 3 CPSEs produce identical ExtractedMaterialAttributes."""
    iocl = "FLG WNRF 4IN 300# A105"
    ongc = "FLANGE, WELDING NECK, 4 INCH, CLASS 300, ASTM A105, ASME B16.5, RF FACING"
    bpcl = "FLG-WN-DN100-PN50-A105-RF"

    a_iocl = extract_attributes(iocl)
    a_ongc = extract_attributes(ongc)
    a_bpcl = extract_attributes(bpcl)

    assert a_iocl.item_type == a_ongc.item_type == a_bpcl.item_type
    assert a_iocl.size_nb_mm == a_ongc.size_nb_mm == a_bpcl.size_nb_mm
    assert a_iocl.pressure_class == a_ongc.pressure_class == a_bpcl.pressure_class
    assert a_iocl.metallurgy == a_ongc.metallurgy == a_bpcl.metallurgy
    assert a_iocl.facing_end == a_ongc.facing_end == a_bpcl.facing_end
