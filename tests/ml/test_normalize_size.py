import pytest

from machine_learning.ner_tagger import _regex_attributes, normalize_size


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('1/2"', 12.7),
        ('3/4"', 19.05),
        ('1 1/2"', 38.1),
        ('4"', 101.6),
        ("4 INCH", 101.6),
        ("DN100", 100.0),
        ("100 MM", 100.0),
        ("100mm NB", 100.0),
    ],
)
def test_normalize_size_supports_common_nominal_size_formats(raw, expected):
    assert normalize_size(raw) == pytest.approx(expected)


def test_regex_attribute_extraction_keeps_quoted_inch_unit():
    assert _regex_attributes('FLANGE 4"').size_nb_mm == pytest.approx(101.6)
