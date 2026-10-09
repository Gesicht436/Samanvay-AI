from machine_learning.ner_tagger import _regex_attributes


def test_longer_metallurgy_names_win_over_contained_short_names():
    assert _regex_attributes("FLANGE 316L").metallurgy == "SS316L"


def test_metallurgy_matches_are_case_insensitive_and_token_bounded():
    assert _regex_attributes("VALVE A105N").metallurgy == "ASTM_A105N"
    assert _regex_attributes("VALVE X3160").metallurgy is None
