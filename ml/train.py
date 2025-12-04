import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import lightgbm as lgb

# Configuration
ARTIFACTS_DIR = Path("artifacts")
MODEL_PATH = ARTIFACTS_DIR / "model.pkl"
RANDOM_SEED = 42

def generate_mock_data(n_samples=1000):
    """
    Generates mock satellite data for training.
    Features: Band 1, Band 2, Band 3 (e.g., RGB/NIR)
    Target: Chlorophyll-a concentration
    """
    np.random.seed(RANDOM_SEED)
    X = np.random.rand(n_samples, 5)  # 5 spectral bands
    # Synthetic relationship: Target = 2*B1 + 0.5*B2^2 + 3*B3*B4 + noise
    y = (
        2 * X[:, 0] 
        + 0.5 * (X[:, 1] ** 2) 
        + 3 * X[:, 2] * X[:, 3] 
        + np.random.normal(0, 0.1, n_samples)
    )
    return X, y

def train():
    print("Generating mock data...")
    X, y = generate_mock_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED)

    models = {
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=RANDOM_SEED),
        "XGBoost": xgb.XGBRegressor(objective="reg:squarederror", random_state=RANDOM_SEED),
        "LightGBM": lgb.LGBMRegressor(random_state=RANDOM_SEED, verbose=-1)
    }

    best_model = None
    best_mse = float("inf")
    best_name = ""

    print("Training models...")
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        print(f"{name} MSE: {mse:.4f}")

        if mse < best_mse:
            best_mse = mse
            best_model = model
            best_name = name

    print(f"\nBest model: {best_name} with MSE: {best_mse:.4f}")

    # Save best model
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train()
