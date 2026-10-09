from pathlib import Path
from typing import Any

from .features import build_features

_DOMAIN_ORDER = ("dim", "met", "pt", "std")


class CompatibilityRanker:
    def __init__(self, model_path: str | Path = "machine_learning/model_weights/reranker.xgb", model: Any = None) -> None:
        self.model = model
        path = Path(model_path)
        if self.model is None and path.is_file():
            try:
                from xgboost import XGBClassifier
            except ImportError as exc:
                raise RuntimeError("Install the optional ML dependencies to load the reranker model") from exc
            self.model = XGBClassifier()
            self.model.load_model(str(path))

    @staticmethod
    def features(
        query: Any,
        candidate: Any,
        cosine: float = 0.0,
        domain_scores: dict[str, float] | None = None,
    ) -> list[float]:
        return build_features(query, candidate, cosine, domain_scores)

    def score(
        self,
        query: Any,
        candidate: Any,
        cosine: float,
        domain_scores: dict[str, float] | None = None,
    ) -> float:
        features = build_features(query, candidate, cosine, domain_scores)
        if self.model is not None:
            probability = float(self.model.predict_proba([features])[0][1])
            return max(0.0, min(1.0, probability))
        structural_match = sum(features[1:]) / (len(features) - 1)
        return max(0.0, min(1.0, 0.5 * features[0] + 0.5 * structural_match))

    def score_batch(self, query: Any, candidates: list[Any]) -> list[float]:
        scores = []
        for candidate in candidates:
            if isinstance(candidate, dict):
                cosine = candidate.get("cosine", candidate.get("similarity", 0.0))
                domain_scores = candidate.get("domain_scores")
            else:
                cosine = getattr(candidate, "cosine", getattr(candidate, "similarity", 0.0))
                domain_scores = getattr(candidate, "domain_scores", None)
            scores.append(self.score(query, candidate, float(cosine), domain_scores))
        return scores
