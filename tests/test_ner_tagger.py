from machine_learning.ner_tagger import extract_attributes


def test_regex_normalization_handles_procurement_abbreviations():
    attributes = extract_attributes('FLG WN RF 4IN 300# A105')

    assert attributes.item_type == "FLANGE"
    assert attributes.size_nb_mm == 101.6
    assert attributes.pressure_class == 300
    assert attributes.metallurgy == "ASTM_A105"
    assert attributes.facing_end == "WELD_NECK"