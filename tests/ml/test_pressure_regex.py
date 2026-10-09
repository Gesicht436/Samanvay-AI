import pytest

from machine_learning.ner_tagger import _regex_attributes


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("VALVE 4 IN CL-300", 300),
        ("VALVE 4 IN CLASS 600", 600),
        ("FLANGE DN100 PN16", 150),
        ("FLANGE 100 MM 900 LB", 900),
        ("FLANGE 100 MM 150#", 150),
    ],
)
def test_pressure_regex_extracts_pressure_rating_forms(description, expected):
    assert _regex_attributes(description).pressure_class == expected
