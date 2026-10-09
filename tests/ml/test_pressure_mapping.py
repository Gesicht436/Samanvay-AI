import pytest

from machine_learning.ner_tagger import normalize_pressure


@pytest.mark.parametrize(
    ("designation", "expected"),
    [
        ("PN6", 150),
        ("PN10", 150),
        ("PN16", 150),
        ("PN25", 300),
        ("PN40", 300),
        ("PN50", 300),
        ("PN63", 600),
        ("PN64", 600),
        ("PN80", 600),
        ("PN100", 600),
        ("PN150", 900),
        ("PN250", 1500),
        ("PN320", 2500),
        ("PN420", 2500),
    ],
)
def test_pn_designations_map_only_to_supported_asme_classes(designation, expected):
    assert normalize_pressure(designation) == expected


def test_unmapped_pn_does_not_masquerade_as_an_asme_class():
    assert normalize_pressure("PN37") is None
    assert normalize_pressure("PN37, CLASS 300") == 300
    assert normalize_pressure("CLASS 300") == 300


@pytest.mark.parametrize(
    ("pn", "expected"),
    [
        (6, 150),
        (10, 150),
        (16, 150),
        (25, 300),
        (40, 300),
        (50, 300),
        (63, 600),
        (64, 600),
        (80, 600),
        (100, 600),
        (150, 900),
        (250, 1500),
        (320, 2500),
        (420, 2500),
    ],
)
def test_pn_class_mapping_respects_designation_boundaries(pn, expected):
    assert normalize_pressure(f"PN {pn}") == expected
    assert normalize_pressure(f"PN-{pn}") == expected
    assert normalize_pressure(f"XPN{pn}") is None
    assert normalize_pressure(f"PN{pn}X") is None
