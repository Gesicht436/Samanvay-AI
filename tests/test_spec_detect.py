import pytest

from ml.vision.spec_detect import detect_en10204_type


@pytest.mark.parametrize(
    "text, expected",
    [
        ("EN 10204 3.1 Certificate", "EN 10204 3.1"),
        ("Inspection certificate EN 10204:2004 - 3.2", "EN 10204 3.2"),
        ("EN10204 3.1B", "EN 10204 3.1"),
        ("EN 10204 / 3.1", "EN 10204 3.1"),
        ("en 10204 type 3.1", "EN 10204 3.1"),
        ("Yield strength 13.2 MPa, C 0.31, 23.15", None),
        ("No standard mentioned", None),
        ("EN 10204 3.1 ... EN 10204 3.2", None),
        ("EN 10204 3.12", None),
        ("", None),
    ],
)
def test_detect_en10204_type(text, expected):
    assert detect_en10204_type(text) == expected
