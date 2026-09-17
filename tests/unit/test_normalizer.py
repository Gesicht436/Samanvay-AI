import pytest
import unicodedata

def normalize_text(text):
    return unicodedata.normalize('NFKC', text)

def test_dialect_mappings():
    mappings = {
        "nut": "NUT",
        "bolt": "BOLT",
        "spanner": "WRENCH"
    }
    assert mappings["spanner"] == "WRENCH"

def test_nfkc_normalization():
    text = "ﬃ"
    normalized = normalize_text(text)
    assert normalized == "ffi"

def test_metadata_extraction_from_normalized_text():
    text = "Flange 100mm 300# RF"
    normalized = normalize_text(text).upper()
    assert "100MM" in normalized
    assert "300#" in normalized
