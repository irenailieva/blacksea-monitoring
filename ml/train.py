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
ARTIFACTS_DIR = Path("ml/artifacts")
MODEL_PATH = ARTIFACTS_DIR / "model.pkl"
RANDOM_SEED = 42

def load_data(path: Path):
    """
    Loads satellite data for training from a CSV file.
    Expected columns: band1, band2, band3, band4, band5, target
    """
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    
    df = pd.read_csv(path)
    
    # Assuming last column is target, or specific column name 'target'
    if 'target' in df.columns:
        y = df['target'].values
        X = df.drop(columns=['target']).values
    else:
        # Fallback: last column is target
        y = df.iloc[:, -1].values
        X = df.iloc[:, :-1].values
        
    return X, y

DATA_PATH = Path("ml/data/train.csv")

def train():
    print(f"Loading data from {DATA_PATH}...")
    try:
        X, y = load_data(DATA_PATH)
    except FileNotFoundError:
        print(f"Error: Data file not found at {DATA_PATH}. Please ensure 'data/train.csv' exists.")
        return
    print(f"Training on {len(X)} samples...")
    
    # Limit training data for dev/testing if it's too large
    MAX_SAMPLES = 10000
    if len(X) > MAX_SAMPLES:
        print(f"Dataset too large. Sampling {MAX_SAMPLES} random rows for faster training.")
        indices = np.random.choice(len(X), MAX_SAMPLES, replace=False)
        X = X[indices]
        y = y[indices]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED)

    models = {
        "RandomForest": RandomForestRegressor(n_estimators=50, n_jobs=-1, random_state=RANDOM_SEED),
        "XGBoost": xgb.XGBRegressor(objective="reg:squarederror", n_jobs=-1, random_state=RANDOM_SEED),
        "LightGBM": lgb.LGBMRegressor(n_jobs=-1, random_state=RANDOM_SEED, verbose=-1)
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
