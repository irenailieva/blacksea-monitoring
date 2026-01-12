import joblib
import numpy as np
from pathlib import Path
from scipy import stats

class WaterQualityModel:
    def __init__(self, rf, xgb_model, lgb_model):
        self.rf = rf
        self.xgb = xgb_model
        self.lgb = lgb_model
        self.mapping = {0: 10, 1: 20, 2: 30} # Sand, Algae, Deep Sea

    @property
    def n_features(self):
        # All models should have same n_features
        # Features: [B2, B3, B4, B8, NDVI, NDWI]
        return 6 

    def _vote(self, X):
        # Soft Voting: Average the probabilities
        # Shape: (n_samples, n_classes)
        prob1 = self.rf.predict_proba(X)
        prob2 = self.xgb.predict_proba(X)
        prob3 = self.lgb.predict_proba(X)
        
        # Average probabilities
        avg_prob = (prob1 + prob2 + prob3) / 3.0
        
        # Take class with highest accumulated probability
        final_pred = np.argmax(avg_prob, axis=1)
        return final_pred

    def predict_one(self, x):
        X = np.array(x, dtype=float).reshape(1, -1)
        if X.shape[1] != self.n_features:
            raise ValueError(f"Expected {self.n_features} features, got {X.shape[1]}. Features should be: [B2, B3, B4, B8, NDVI, NDWI]")
        pred = self._vote(X)[0]
        return float(self.mapping.get(pred, 30)) # Default to deep sea if unknown

    def predict_batch(self, X):
        X = np.array(X, dtype=float)
        if X.ndim != 2 or X.shape[1] != self.n_features:
            raise ValueError(f"Expected 2D array with {self.n_features} features per sample, got shape {X.shape}. Features should be: [B2, B3, B4, B8, NDVI, NDWI]")
        preds = self._vote(X)
        return [float(self.mapping.get(p, 30)) for p in preds]

    def explain_one(self, x):
        # Placeholder for explanation logic if needed later
        # SHAP or feature importance could be added here
        yhat = self.predict_one(x)
        return [0.0] * self.n_features, 0.0, yhat

def load_model(artifact_dir: Path) -> WaterQualityModel:
    if not artifact_dir.exists():
        raise FileNotFoundError(f"Artifacts directory not found: {artifact_dir}")
    
    try:
        rf = joblib.load(artifact_dir / "rf_model.pkl")
        xgb_model = joblib.load(artifact_dir / "xgb_model.pkl")
        lgb_model = joblib.load(artifact_dir / "lgb_model.pkl")
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Missing model file: {e}")
        
    return WaterQualityModel(rf, xgb_model, lgb_model)
