from machine_learning.reranker.train import train_from_rows


class SyntheticClassifier:
    trained_features = None

    def __init__(self, **kwargs):
        self.options = kwargs

    def fit(self, features, labels, eval_set, verbose):
        type(self).trained_features = features
        self.eval_set = eval_set

    def predict_proba(self, features):
        return [[1 - value[0], value[0]] for value in features]

    def save_model(self, path):
        with open(path, "w", encoding="utf-8") as model_file:
            model_file.write("synthetic")


def test_train_reranker_smoke_test_uses_synthetic_rows_and_saves_model(tmp_path):
    rows = [
        {
            "query": "VALVE DN100 CLASS 300",
            "candidate": "VALVE DN100 CLASS 300",
            "cosine": 0.9 if label else 0.1,
            "label": label,
        }
        for label in (0, 1)
        for _ in range(5)
    ]
    output = tmp_path / "synthetic-reranker.xgb"

    auc = train_from_rows(rows, output, model_factory=SyntheticClassifier)

    assert 0.0 <= auc <= 1.0
    assert output.read_text(encoding="utf-8") == "synthetic"
    assert len(SyntheticClassifier.trained_features[0]) == 13


def test_train_reranker_uses_separate_domain_cosines(tmp_path):
    rows = [
        {
            "query": "query",
            "candidate": "candidate",
            "cosine": 0.7,
            "dim_cosine": 0.91,
            "met_cosine": 0.82,
            "pt_cosine": 0.73,
            "std_cosine": 0.64,
            "label": label,
        }
        for label in (0, 1)
        for _ in range(5)
    ]

    train_from_rows(rows, tmp_path / "domains.xgb", model_factory=SyntheticClassifier)

    assert SyntheticClassifier.trained_features[0][-4:] == [0.91, 0.82, 0.73, 0.64]
