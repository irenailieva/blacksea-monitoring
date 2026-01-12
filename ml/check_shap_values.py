import pandas as pd
import numpy as np
import shap
import joblib
from pathlib import Path

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
DATA_PATH = Path(__file__).parent / "dataset.csv"

def check_shap():
    print("Loading data...")
    df = pd.read_csv(DATA_PATH)
    
    # Reconstruct features exactly as in training
    blue = df['band_1'].values.astype(float)
    green = df['band_2'].values.astype(float)
    red = df['band_3'].values.astype(float)
    nir = df['band_4'].values.astype(float)
    
    if 'ndvi' in df.columns and 'ndwi' in df.columns:
        print("Using pre-calculated indices.")
        ndvi = df['ndvi'].values.astype(float)
        ndwi = df['ndwi'].values.astype(float)
        X = np.column_stack([blue, green, red, nir, ndvi, ndwi])
    else:
        print("Dataset missing indices!")
        return

    feature_names = ['Blue', 'Green', 'Red', 'NIR', 'NDVI', 'NDWI']

    print("Loading LightGBM model...")
    model_path = ARTIFACTS_DIR / "lgb_model.pkl"
    if not model_path.exists():
        print("Model not found.")
        return
        
    lgb_model = joblib.load(model_path)
    
    print("Calculating SHAP values...")
    explainer = shap.TreeExplainer(lgb_model)
    shap_values = explainer.shap_values(X)
    
    # Debug: Print type and shape
    print(f"SHAP values type: {type(shap_values)}")
    
    if isinstance(shap_values, list):
         # Old behavior or list output
         print(f"SHAP values list length: {len(shap_values)}")
         if len(shap_values) > 1:
             vals = shap_values[1] # Class 1
         else:
             vals = shap_values[0]
    elif len(shap_values.shape) == 3:
         # (n_samples, n_features, n_classes)
         print(f"SHAP values 3D array shape: {shap_values.shape}")
         # Take Class 1 (Index 1)
         vals = shap_values[:, :, 1]
    else:
         # Binary
         print(f"SHAP values 2D array shape: {shap_values.shape}")
         vals = shap_values

    # Calculate mean absolute SHAP value for each feature
    # vals shape should be (n_samples, n_features) from above
    print(f"Processing vals shape: {vals.shape}")
    mean_abs_shap = np.mean(np.abs(vals), axis=0)
    
    print(f"Features: {feature_names}")
    print(f"Computed Importance Shape: {mean_abs_shap.shape}")

    if len(mean_abs_shap) != len(feature_names):
        print("Error: Feature count mismatch!")
        return

    # Create DataFrame for nice printing
    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': mean_abs_shap
    })
    
    # Sort descending
    importance_df = importance_df.sort_values(by='Importance', ascending=False)
    
    print("\n--- SHAP Feature Importance for Class 1 (Vegetation) ---")
    print(importance_df)
    print("------------------------------------------------------")

if __name__ == "__main__":
    check_shap()
