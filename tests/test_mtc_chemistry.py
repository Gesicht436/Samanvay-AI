from backend.app.ingestion import parse_mtc_certificate
from backend.app.ingestion.certificate import parse_mtc


def test_mtc_parser_extracts_inline_and_table_chemistry():
    record = parse_mtc(
        """Certificate No: MTC-22
Material Grade: ASTM A182 F316
Chemical Composition (%)
C Mn Si S P Cr Ni Mo
0.03 1.50 0.45 0.010 0.030 16.8 10.2 2.1
"""
    )

    values = {item.element: item.value for item in record.chemical_composition}
    assert record.cert_no == "MTC-22"
    assert values["Carbon"] == 0.03
    assert values["Chromium"] == 16.8
    assert values["Nickel"] == 10.2
    assert values["Molybdenum"] == 2.1


def test_mtc_parser_extracts_chemistry_label_value_pairs_and_mechanical_properties():
    record = parse_mtc(
        """Chemical Analysis
Carbon: 0.18 %
Manganese: 0.75 %
Chromium: 18.2 %
Mechanical Properties
Yield Strength (MPa): 310
Tensile Strength (MPa): 525
Elongation (%): 29.5
"""
    )

    assert {item.element: item.value for item in record.chemical_composition} == {
        "Carbon": 0.18,
        "Manganese": 0.75,
        "Chromium": 18.2,
    }
    assert {item.property: item.value for item in record.mechanical_properties} == {
        "yield_strength": 310.0,
        "tensile_strength": 525.0,
        "elongation": 29.5,
    }


def test_api_metadata_includes_parsed_chemistry_without_losing_existing_fields():
    metadata = parse_mtc_certificate(
        """Certificate No: MTC-23
Chemical Analysis
Carbon: 0.12 %
"""
    )

    assert metadata["certificate_number"] == "MTC-23"
    assert metadata["chemical_composition"] == [{"element": "Carbon", "value": 0.12, "unit": "%"}]
