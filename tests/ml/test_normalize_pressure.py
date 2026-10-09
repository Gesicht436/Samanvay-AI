import pytest

from machine_learning.ner_tagger import normalize_pressure


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("150#", 150),
        ("CLASS 300", 300),
        ("CL-600", 600),
        ("PN16", 150),
        ("PN100", 600),
        ("PN250", 1500),
    ],
)
def test_normalize_pressure_converts_pressure_designations(raw, expected):
    assert normalize_pressure(raw) == expected
