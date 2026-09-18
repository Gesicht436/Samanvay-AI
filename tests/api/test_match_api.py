import pytest
from ml.ner.normalizer import DialectNormalizer
from rules.tolerance import evaluate_pair
from ml.ranking.ranker import CompatibilityRanker


def test_normalizer_and_matching_pipeline():
    normalizer = DialectNormalizer()
    norm = normalizer.normalize("FLG WNRF 4IN 300# A105 SCH 40")

    assert norm.get("item_type") == "FLANGE"
    assert norm.get("size_nb_mm") == 100.0
    assert norm.get("pressure_class") == 300
    assert "A105" in norm.get("metallurgy", "")

    query_part = {
        "item_type": "FLANGE",
        "size_nb_mm": 100.0,
        "pressure_class": 300,
        "metallurgy": "ASTM A105",
        "properties": {"facing": "RF"},
    }

    # Identical candidate
    cand_identical = {
        "item_type": "FLANGE",
        "size_nb_mm": 100.0,
        "pressure_class": 300,
        "metallurgy": "ASTM A105",
        "properties": {"facing": "RF"},
    }
    result_identical = evaluate_pair(query_part, cand_identical)
    assert result_identical.is_compatible is True
    assert "TIER_1" in result_identical.compatibility_tier.name

    # Incompatible size
    cand_wrong_size = {
        "item_type": "FLANGE",
        "size_nb_mm": 150.0,
        "pressure_class": 300,
        "metallurgy": "ASTM A105",
        "properties": {"facing": "RF"},
    }
    result_wrong_size = evaluate_pair(query_part, cand_wrong_size)
    assert result_wrong_size.is_compatible is False
    assert len(result_wrong_size.rule_violations) > 0
    assert "DIM" in str(result_wrong_size.rule_violations[0].module_name)


def test_compatibility_ranker_scoring():
    ranker = CompatibilityRanker()
    q = {"item_type": "VALVE", "size_nb_mm": 50.0, "pressure_class": 150, "metallurgy": "A216 WCB"}
    c1 = {"item_type": "VALVE", "size_nb_mm": 50.0, "pressure_class": 150, "metallurgy": "A216 WCB"}
    c2 = {"item_type": "VALVE", "size_nb_mm": 50.0, "pressure_class": 300, "metallurgy": "A216 WCB"}

    score1 = ranker.predict(q, c1)
    score2 = ranker.predict(q, c2)

    assert score1 >= 0.80
    assert isinstance(score2, float)
