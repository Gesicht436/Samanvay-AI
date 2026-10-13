"""Unit tests for postprocessing and domain thesaurus substitution."""

from ml.vision.postprocessing import (
    apply_domain_thesaurus,
    fix_numeric_ambiguities,
    postprocess_token,
    sanitize_text,
)


def test_sanitize_text_strips_control_chars_and_extra_spaces():
    raw = "  HEAT  \x00 NO:   H-99482 \n "
    assert sanitize_text(raw) == "HEAT NO: H-99482"


def test_fix_numeric_ambiguities():
    assert fix_numeric_ambiguities("0.O25") == "0.025"
    assert fix_numeric_ambiguities("1.l5") == "1.15"


def test_apply_domain_thesaurus_expands_abbreviations():
    assert apply_domain_thesaurus("CS RED WELD") == "CARBON STEEL REDUCER WELD"
    assert apply_domain_thesaurus("SA105N PIPE") == "ASTM A105 PIPE"


def test_postprocess_token_preserves_raw_string():
    clean, raw = postprocess_token("  CS \x00 PIPE ")
    assert clean == "CARBON STEEL PIPE"
    assert raw == "  CS \x00 PIPE "
