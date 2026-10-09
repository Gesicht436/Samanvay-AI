import subprocess
import sys

from machine_learning.reranker.features import build_features


def test_feature_vector_has_thirteen_deterministic_values():
    query = {"item_type": "VALVE", "size_nb_mm": 100, "pressure_class": 300}
    candidate = {"item_type": "VALVE", "size_nb_mm": 100, "pressure_class": 600}

    features = build_features(query, candidate, cosine=0.8)

    assert len(features) == 13
    assert all(0.0 <= value <= 1.0 for value in features)
    assert features == build_features(query, candidate, cosine=0.8)


def test_domain_cosines_are_independent_feature_values():
    domain_scores = {"dim": 0.91, "met": 0.82, "pt": 0.73, "std": 0.64}

    features = build_features({}, {}, cosine=0.77, domain_scores=domain_scores)

    assert len(features) == 13
    assert features[0] == 0.77
    assert features[9:] == [0.91, 0.82, 0.73, 0.64]


def test_attribute_coverage_feature_is_meaningful_and_stable_across_processes():
    code = (
        "from machine_learning.reranker.features import build_features; "
        "print(build_features({'item_type':'VALVE','size_nb_mm':100}, "
        "{'item_type':'VALVE','size_nb_mm':100}, 0.8)[8])"
    )
    first = subprocess.check_output([sys.executable, "-c", code], text=True).strip()
    second = subprocess.check_output([sys.executable, "-c", code], text=True).strip()

    assert first == second
    assert float(first) == 2 / 6
