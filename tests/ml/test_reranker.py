from machine_learning.reranker import CompatibilityRanker


def test_ranker_uses_documented_deterministic_fallback():
    ranker = CompatibilityRanker(model_path="missing-reranker-model.xgb")
    query = {"item_type": "VALVE", "size_nb_mm": 100, "pressure_class": 300}
    candidate = {"item_type": "VALVE", "size_nb_mm": 100, "pressure_class": 600}
    cosine = 0.8

    features = ranker.features(query, candidate, cosine)
    expected = 0.5 * cosine + 0.5 * sum(features[1:]) / (len(features) - 1)

    assert ranker.score(query, candidate, cosine) == expected


def test_score_batch_returns_scores_in_candidate_order():
    ranker = CompatibilityRanker(model_path="missing-reranker-model.xgb")
    candidates = [
        {"item_type": "VALVE", "size_nb_mm": 100, "pressure_class": 300, "similarity": 0.8},
        {"item_type": "FLANGE", "size_nb_mm": 150, "pressure_class": 150, "similarity": 0.7},
    ]

    scores = ranker.score_batch({"item_type": "VALVE", "size_nb_mm": 100}, candidates)

    assert len(scores) == 2
    assert scores[0] > scores[1]
