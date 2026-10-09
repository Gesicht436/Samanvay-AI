from OCR.normalization import DIALECT_THESAURUS, normalize_text


def test_dialect_thesaurus_contains_at_least_forty_entries():
    assert len(DIALECT_THESAURUS) >= 40


def test_common_indian_procurement_and_material_dialects_expand():
    normalized = normalize_text("VLV GV 4IN CL300 MS EIL OISD GeM CPPP MESC")

    for phrase in (
        "VALVE",
        "GATE VALVE",
        "SIZE_IN=4",
        "CLASS=300",
        "MILD STEEL",
        "ENGINEERS INDIA LIMITED",
        "OIL INDUSTRY SAFETY DIRECTORATE",
        "GOVERNMENT E-MARKETPLACE",
        "CENTRAL PUBLIC PROCUREMENT PORTAL",
        "MATERIAL ENGINEERING SPECIFICATION",
    ):
        assert phrase in normalized


def test_metallurgy_grade_tokens_are_not_broken_by_ss_expansion():
    assert normalize_text("SS316L") == "SS316L"


def test_ambiguous_is_token_in_ordinary_text_is_not_expanded():
    assert normalize_text("THIS IS A FLANGE") == "THIS IS A FLANGE"
