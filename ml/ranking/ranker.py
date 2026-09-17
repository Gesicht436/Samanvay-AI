import os
from typing import List
from ml.ranking.feature_extract import build_feature_vector

class CompatibilityRanker:
    def __init__(self, model_path="model.xgb"):
        self.model = None
        if os.path.exists(model_path):
            try:
                import xgboost as xgb
                self.model = xgb.Booster()
                self.model.load_model(model_path)
            except ImportError:
                pass
                
    def predict(self, query: dict, candidate: dict) -> float:
        features = build_feature_vector(query, candidate)
        if self.model:
            import xgboost as xgb
            dmatrix = xgb.DMatrix([features])
            return float(self.model.predict(dmatrix)[0])
            
        # Fallback: Weighted average of cosines
        weights = [0.4, 0.3, 0.2, 0.1]
        return float(sum(f * w for f, w in zip(features, weights)))
        
    def predict_batch(self, query: dict, candidates: List[dict]) -> List[float]:
        return [self.predict(query, c) for c in candidates]
