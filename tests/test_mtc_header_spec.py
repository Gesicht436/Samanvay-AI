from ml.vision.mtc_parser import MTCParser


def test_measurement_13_2_does_not_make_a_3_1_certificate_3_2():
    text = "EN 10204 3.1 Certificate No: ABC-123\nYield strength 13.2 MPa"
    assert MTCParser().parse_header(text)["specification"] == "EN 10204 3.1"


def test_unstated_type_returns_none():
    text = "Heat No: H-1001\nYield strength 13.2 MPa, tensile 23.15"
    assert MTCParser().parse_header(text)["specification"] is None


def test_explicit_3_2_is_detected():
    text = "Inspection certificate EN 10204 3.2 No: XYZ-9"
    assert MTCParser().parse_header(text)["specification"] == "EN 10204 3.2"
