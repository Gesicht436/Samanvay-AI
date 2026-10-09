from machine_learning.ner_tagger import ENTITY_TYPES, _regex_attributes


def test_ner_covers_indian_procurement_and_material_fields():
    text = (
        "VALVE DN100 CLASS 300 ASTM A216 WCB IS 1239 OISD-STD-141 "
        "EIL SPEC 6-44-001 GeM Category 40141600 CPPP Tender 2024_MES_123 "
        "MESC 76.10.01 Manufacturer Acme Product Form CAST Coating FBE "
        "Inspection Class B Document No DOC-77 Project Paradip "
        "End Connection FLANGED Temperature 120 C PO-77 Certificate MTC-99"
    )
    attributes = _regex_attributes(text)

    assert len(ENTITY_TYPES) >= 18
    assert attributes.indian_standard == "IS 1239"
    assert attributes.oisd_standard == "OISD-STD-141"
    assert attributes.eil_specification == "EIL SPEC 6-44-001"
    assert attributes.gem_category == "40141600"
    assert attributes.cppp_tender_id == "2024_MES_123"
    assert attributes.mesc_code == "76.10.01"
    assert attributes.manufacturer == "Acme"
    assert attributes.product_form == "CAST"
    assert attributes.coating == "FBE"
    assert attributes.inspection_class == "B"
    assert attributes.document_number == "DOC-77"
    assert attributes.project == "Paradip"
    assert attributes.end_connection == "FLANGED"
    assert attributes.temperature_rating == 120
    assert attributes.purchase_order == "PO-77"
    assert attributes.certificate_number == "MTC-99"
    assert attributes.item_type == "VALVE"


def test_gem_bid_number_is_not_mistaken_for_a_category():
    attributes = _regex_attributes("GeM Bid No GEM/2026/B/123")

    assert attributes.gem_category is None
    assert attributes.gem_bid_number == "GEM/2026/B/123"


def test_indian_standard_recognition_does_not_capture_common_word_is():
    assert _regex_attributes("THIS IS A FLANGE").indian_standard is None
