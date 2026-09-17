from typing import List
from ml.ranking.feature_extract import compute_subvector_cosines

class ShapExplainer:
    def __init__(self, model_path="model.xgb"):
        self.explainer = None
        try:
            import shap
            import xgboost as xgb
            import os
            if os.path.exists(model_path):
                model = xgb.Booster()
                model.load_model(model_path)
                self.explainer = shap.TreeExplainer(model)
        except ImportError:
            pass
            
    def explain(self, query: dict, candidate: dict, score: float) -> List[str]:
        # Fallback heuristic explanations
        explanations = []
        cosines = compute_subvector_cosines(query, candidate)
        
        if cosines["dimensional"] > 0.95:
            explanations.append("Score boosted due to exact dimensional match")
        elif cosines["dimensional"] < 0.5:
            explanations.append("Score penalized heavily due to dimensional variance")
            
        if cosines["metallurgy"] > 0.9:
            explanations.append("High metallurgical compatibility")
            
        return explanations
