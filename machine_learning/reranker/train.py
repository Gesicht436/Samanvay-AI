import math
import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

from machine_learning.reranker.features import build_features
from machine_learning.subvectors import DOMAINS


def _validation_split(rows: list[dict[str, Any]], seed: int = 42) -> tuple[list[int], list[int]]:
    grouped: dict[int, list[int]] = {}
    for index, row in enumerate(rows):
        label = int(row["label"])
        if label not in (0, 1):
            raise ValueError(f"label must be 0 or 1, got {label}")
        grouped.setdefault(label, []).append(index)
    if len(grouped) != 2 or min(map(len, grouped.values())) < 2:
        raise ValueError("reranker training data needs at least two rows for each label")

    randomizer = random.Random(seed)
    train_indices: list[int] = []
    validation_indices: list[int] = []
    for indices in grouped.values():
        randomizer.shuffle(indices)
        validation_count = max(1, math.ceil(len(indices) * 0.2))
        validation_indices.extend(indices[:validation_count])
        train_indices.extend(indices[validation_count:])
    return train_indices, validation_indices


def _auc(labels: list[int], probabilities: list[float]) -> float:
    positives = [score for label, score in zip(labels, probabilities) if label == 1]
    negatives = [score for label, score in zip(labels, probabilities) if label == 0]
    if not positives or not negatives:
        raise ValueError("validation data must contain both labels to calculate AUC")
    wins = sum(1.0 if positive > negative else 0.5 if positive == negative else 0.0 for positive in positives for negative in negatives)
    return wins / (len(positives) * len(negatives))


def train_from_rows(
    rows: list[dict[str, Any]],
    output_path: str | Path = "machine_learning/model_weights/reranker.xgb",
    model_factory: Callable[..., Any] | None = None,
) -> float:
    if model_factory is None:
        try:
            from xgboost import XGBClassifier
        except ImportError as exc:
            raise RuntimeError("Install the optional ML dependencies to train the reranker") from exc
        model_factory = XGBClassifier

    train_indices, validation_indices = _validation_split(rows)
    features = [
        build_features(
            row["query"],
            row["candidate"],
            float(row["cosine"]),
            {
                domain: float(row.get(f"{domain}_cosine", row["cosine"]))
                for domain in DOMAINS
            },
        )
        for row in rows
    ]
    labels = [int(row["label"]) for row in rows]
    train_features = [features[index] for index in train_indices]
    train_labels = [labels[index] for index in train_indices]
    validation_features = [features[index] for index in validation_indices]
    validation_labels = [labels[index] for index in validation_indices]

    model = model_factory(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.05,
        objective="binary:logistic",
        eval_metric="auc",
        early_stopping_rounds=20,
        random_state=42,
    )
    model.fit(
        train_features,
        train_labels,
        eval_set=[(validation_features, validation_labels)],
        verbose=False,
    )
    probabilities = [float(value[1]) for value in model.predict_proba(validation_features)]
    auc = _auc(validation_labels, probabilities)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(destination))
    print(f"Validation AUC: {auc:.4f}")
    return auc


def train(
    train_file: str | Path = "data/ml_training/reranker_pairs.parquet",
    output_path: str | Path = "machine_learning/model_weights/reranker.xgb",
) -> float:
    import polars as pl

    frame = pl.read_parquet(train_file)
    required = {"query", "candidate", "cosine", "label"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"reranker parquet missing required columns: {', '.join(sorted(missing))}")
    return train_from_rows(frame.to_dicts(), output_path)


if __name__ == "__main__":
    train()
