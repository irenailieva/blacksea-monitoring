import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb
import lightgbm as lgb
import warnings

# Configuration
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
DATA_PATH = Path(__file__).parent / "dataset.csv"
RANDOM_SEED = 42

# Ensure artifacts directory exists
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def cleanup_labels(val):
    """Maps class IDs to 0, 1, 2."""
    if val == 0: return 0 # Sand / Shallow Water
    if val == 1: return 1 # Rocks / Algae
    if val == 2: return 2 # Deep Sea
    return 2 # Fallback

def train():
    print(f"Loading data from {DATA_PATH}...")
    if not DATA_PATH.exists():
        print(f"Error: Data file not found at {DATA_PATH}.")
        return

    df = pd.read_csv(DATA_PATH)
    
    # Preprocess labels
    if 'class_id' not in df.columns:
        print("Error: 'class_id' column missing in dataset.")
        return

    y = df['class_id'].apply(cleanup_labels).values.astype(int)
    
    # Select features
    feature_cols = ['band_1', 'band_2', 'band_3', 'band_4']
    if not all(col in df.columns for col in feature_cols):
        print(f"Error: Missing feature columns. Expected: {feature_cols}")
        return
        
    X = df[feature_cols].values

    print(f"Training on {len(X)} samples with {len(feature_cols)} features...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y)

    # 1. Random Forest
    print("Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=50, max_depth=10, n_jobs=-1, class_weight='balanced', random_state=RANDOM_SEED)
    rf.fit(X_train, y_train)
    rf_acc = accuracy_score(y_test, rf.predict(X_test))
    print(f"RF Accuracy: {rf_acc:.4f}")

    # 2. XGBoost
    print("Training XGBoost...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=50, max_depth=6, objective='multi:softmax', num_class=3,
        tree_method="hist", n_jobs=-1, random_state=RANDOM_SEED
    )
    xgb_model.fit(X_train, y_train)
    xgb_acc = accuracy_score(y_test, xgb_model.predict(X_test))
    print(f"XGB Accuracy: {xgb_acc:.4f}")

    # 3. LightGBM
    print("Training LightGBM...")
    lgb_model = lgb.LGBMClassifier(
        n_estimators=50, num_leaves=31, objective='multiclass', 
        class_weight='balanced', verbose=-1, random_state=RANDOM_SEED, n_jobs=-1
    )
    lgb_model.fit(X_train, y_train)
    lgb_acc = accuracy_score(y_test, lgb_model.predict(X_test))
    print(f"LGB Accuracy: {lgb_acc:.4f}")

    # Save models
    print("Saving models...")
    joblib.dump(rf, ARTIFACTS_DIR / "rf_model.pkl")
    joblib.dump(xgb_model, ARTIFACTS_DIR / "xgb_model.pkl")
    joblib.dump(lgb_model, ARTIFACTS_DIR / "lgb_model.pkl")
    
    print(f"✅ Models saved to {ARTIFACTS_DIR}")

if __name__ == "__main__":
    train()
