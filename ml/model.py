import json
import numpy as np
from pathlib import Path

class LinearModel:
    def __init__(self, weights, bias):
        self.w = np.array(weights, dtype=float)
        self.b = float(bias)

    @property
    def n_features(self):
        return self.w.shape[0]

    def predict_one(self, x):
        x = np.array(x, dtype=float)
        if x.shape[0] != self.w.shape[0]:
            raise ValueError(f"Expected {self.w.shape[0]} features, got {x.shape[0]}")
        return float(self.w.dot(x) + self.b)

    def predict_batch(self, X):
        X = np.array(X, dtype=float)
        if X.shape[1] != self.w.shape[0]:
            raise ValueError(f"Expected {self.w.shape[0]} features, got {X.shape[1]}")
        return list((X @ self.w) + self.b)

    def explain_one(self, x):
        x = np.array(x, dtype=float)
        if x.shape[0] != self.w.shape[0]:
            raise ValueError(f"Expected {self.w.shape[0]} features, got {x.shape[0]}")
        # Проста линейна „обяснимост“: принос = w_i * x_i
        contrib = self.w * x
        yhat = float(contrib.sum() + self.b)
        return list(map(float, contrib)), float(self.b), yhat

def load_model(path: Path) -> LinearModel:
    data = json.loads(path.read_text(encoding="utf-8"))
    return LinearModel(weights=data["weights"], bias=data["bias"])
