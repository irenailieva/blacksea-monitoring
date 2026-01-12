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
from utils import prepare_features

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
    
    # Select base features (spectral bands)
    base_cols = ['band_1', 'band_2', 'band_3', 'band_4']
    if not all(col in df.columns for col in base_cols):
        print(f"Error: Missing feature columns. Expected: {base_cols}")
        return
    
    # Extract bands (assuming Sentinel-2: B2=Blue, B3=Green, B4=Red, B8=NIR)
    # band_1 = Blue (B2), band_2 = Green (B3), band_3 = Red (B4), band_4 = NIR (B8)
    blue = df['band_1'].values.astype(float)
    green = df['band_2'].values.astype(float)
    red = df['band_3'].values.astype(float)
    nir = df['band_4'].values.astype(float)
    
    # Check if indices are already in dataset (Enriched)
    if 'ndvi' in df.columns and 'ndwi' in df.columns:
        print("Using pre-calculated indices from dataset.")
        ndvi = df['ndvi'].values.astype(float)
        ndwi = df['ndwi'].values.astype(float)
        # Re-stack manually
        X = np.column_stack([blue, green, red, nir, ndvi, ndwi])
    else:
        print("Calculating indices on the fly...")
        X = prepare_features(blue, green, red, nir)

    print(f"Training on {len(X)} samples with 6 features: [B2, B3, B4, B8, NDVI, NDWI]...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y)
    
    # Update Class Names for Plots
    class_names = ['Non-vegetated', 'Vegetation', 'Deep Sea'] # 0, 1, 2

    # 1. Random Forest
    print("Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=50, max_depth=10, n_jobs=-1, class_weight='balanced', random_state=RANDOM_SEED)
    rf.fit(X_train, y_train)
    rf_acc = accuracy_score(y_test, rf.predict(X_test))
    print(f"RF Accuracy: {rf_acc:.4f}")

    # 2. XGBoost
    print("Training XGBoost...")
    # Multiclass
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

    # --- Voting Classifier Evaluation (Soft Voting) ---
    print("\nEvaluating Voting Classifier (Soft Voting)...")
    
    # Get probabilities from each model
    prob1 = rf.predict_proba(X_test)
    prob2 = xgb_model.predict_proba(X_test)
    prob3 = lgb_model.predict_proba(X_test)
    
    # Average probabilities
    avg_prob = (prob1 + prob2 + prob3) / 3.0
    
    # Take class with highest accumulated probability
    y_pred_ensemble = np.argmax(avg_prob, axis=1)
    
    ensemble_acc = accuracy_score(y_test, y_pred_ensemble)
    print(f"🏆 Soft Voting Ensemble Accuracy: {ensemble_acc:.4f}")

    # --- Visualization ---
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.metrics import confusion_matrix
    import shap

    print("Generating visualizations...")

    # 1. Confusion Matrix (Ensemble)
    cm = confusion_matrix(y_test, y_pred_ensemble)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names,
                yticklabels=class_names)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix (Voting Ensemble)')
    plt.savefig(ARTIFACTS_DIR / "confusion_matrix.png")
    plt.close()
    print(f"✅ Confusion Matrix (Ensemble) saved to {ARTIFACTS_DIR / 'confusion_matrix.png'}")

    # 2. SHAP Values (using LightGBM as proxy for feature importance)
    # Use TreeExplainer for LightGBM
    explainer = shap.TreeExplainer(lgb_model)
    shap_values = explainer.shap_values(X_test)
    
    # Summary Plot (Bar Chart for Simplicity)
    plt.figure()
    
    # Feature names: B2, B3, B4, B8, NDVI, NDWI
    feature_names = ['Blue', 'Green', 'Red', 'NIR', 'NDVI', 'NDWI']
    
    # Check if shap_values is list (multiclass) or array (binary)
    if isinstance(shap_values, list):
        # Taking class 1 (Vegetation/Algae) for explanation
        # Summing absolute SHAP values for global importance
        vals = shap_values[1]
    else:
        vals = shap_values

    # Plot bar chart of feature importance
    shap.summary_plot(vals, X_test, feature_names=feature_names, plot_type="bar", show=False)
    plt.title("Feature Importance (SHAP) - Class: Vegetation")
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "shap_summary.png")
    plt.close()
    print(f"✅ SHAP summary saved to {ARTIFACTS_DIR / 'shap_summary.png'}")

if __name__ == "__main__":
    train()
