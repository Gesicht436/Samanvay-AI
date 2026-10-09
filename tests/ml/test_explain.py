import sys
from types import SimpleNamespace

from machine_learning.explain import explain
from machine_learning.reranker.features import build_features


class FakeBooster:
    def predict(self, matrix, pred_contribs=False, output_margin=False):
        values = matrix.values
        if pred_contribs:
            return [[*values[0], 0.25]]
        return [sum(values[0]) + 0.25]


class FakeModel:
    def get_booster(self):
        return FakeBooster()


def test_explanations_describe_good_matches_and_contributions_sum(monkeypatch):
    monkeypatch.setitem(sys.modules, "xgboost", SimpleNamespace(DMatrix=lambda values: SimpleNamespace(values=values)))
    query = {"item_type": "VALVE", "size_nb_mm": 100, "pressure_class": 300}
    candidate = {"item_type": "VALVE", "size_nb_mm": 100, "pressure_class": 600}

    reasons = explain(query, candidate, FakeModel())
    features = build_features(query, candidate)
    matrix = sys.modules["xgboost"].DMatrix([features])
    contributions = FakeModel().get_booster().predict(matrix, pred_contribs=True)[0]
    output_margin = FakeModel().get_booster().predict(matrix, output_margin=True)[0]

    assert any("Exact size match (100.0 mm)" in reason for reason in reasons)
    assert any("Pressure class upgrade (300 → 600)" in reason for reason in reasons)
    assert abs(sum(contributions) - output_margin) <= 1e-6


def test_explanations_identify_size_and_pressure_downgrades(monkeypatch):
    monkeypatch.setitem(sys.modules, "xgboost", SimpleNamespace(DMatrix=lambda values: SimpleNamespace(values=values)))

    reasons = explain(
        {"size_nb_mm": 100, "pressure_class": 600},
        {"size_nb_mm": 150, "pressure_class": 300},
        FakeModel(),
    )

    assert any("Size mismatch" in reason for reason in reasons)
    assert any("Pressure class downgrade (600 → 300)" in reason for reason in reasons)
