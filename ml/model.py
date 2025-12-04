import joblib
import numpy as np
from pathlib import Path

class EnsembleModel:
    def __init__(self, model):
        self.model = model

    @property
    def n_features(self):
        # Try to infer number of features
        if hasattr(self.model, "n_features_in_"):
            return self.model.n_features_in_
        if hasattr(self.model, "n_features"): # XGBoost
            return self.model.n_features
        return -1 # Unknown

    def predict_one(self, x):
        x = np.array(x, dtype=float).reshape(1, -1)
        return float(self.model.predict(x)[0])

    def predict_batch(self, X):
        X = np.array(X, dtype=float)
        return list(self.model.predict(X))

    def explain_one(self, x):
        # Simple feature importance based explanation if available
        x = np.array(x, dtype=float)
        
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            # Simple contribution approximation: importance * value
            # Note: This is NOT SHAP, but a lightweight proxy for now.
            contrib = importances * x
            bias = 0.0 # Tree models don't have a single bias term like linear models
            yhat = self.predict_one(x)
            return list(map(float, contrib)), float(bias), float(yhat)
        
        # Fallback if no feature importance
        yhat = self.predict_one(x)
        return [0.0] * len(x), 0.0, yhat

def load_model(path: Path) -> EnsembleModel:
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    
    # Load using joblib (standard for sklearn/xgboost/lightgbm)
    model = joblib.load(path)
    return EnsembleModel(model)
