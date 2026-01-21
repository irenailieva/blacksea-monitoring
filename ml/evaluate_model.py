import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import shap
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

# Configuration
BASE_DIR = Path("/app")
DATASET_PATH = BASE_DIR / "dataset.csv"
ARTIFACTS_DIR = BASE_DIR / "artifacts"

def load_models():
    print("Loading models...")
    rf = joblib.load(ARTIFACTS_DIR / "rf_model.pkl")
    xgb = joblib.load(ARTIFACTS_DIR / "xgb_model.pkl")
    lgb = joblib.load(ARTIFACTS_DIR / "lgb_model.pkl")
    return rf, xgb, lgb

def evaluate():
    # 1. Load Data
    print(f"Loading data from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)
    
    # Check for indices
    if 'ndvi' in df.columns and 'ndwi' in df.columns:
        feature_cols = ['band_1', 'band_2', 'band_3', 'band_4', 'ndvi', 'ndwi']
    else:
        # Fallback if enrichment missing (unlikely given flow)
        feature_cols = ['band_1', 'band_2', 'band_3', 'band_4']
        
    X = df[feature_cols].values
    y = df['class_id'].values
    
    # 2. Split (Fresh Split)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Eval Set: {len(X_test)} samples")
    
    # 3. Load Models
    rf, xgb_model, lgb_model = load_models()
    
    # 4. Soft Voting Prediction
    print("Predicting (Soft Voting)...")
    prob1 = rf.predict_proba(X_test)
    prob2 = xgb_model.predict_proba(X_test)
    prob3 = lgb_model.predict_proba(X_test)
    
    avg_prob = (prob1 + prob2 + prob3) / 3.0
    y_pred_ensemble = np.argmax(avg_prob, axis=1)
    
    acc = accuracy_score(y_test, y_pred_ensemble)
    print(f"🏆 Evaluation Accuracy: {acc:.4f}")
    
    # 5. Confusion Matrix
    print("Generating Confusion Matrix...")
    class_names = ['Abiotic', 'Vegetation', 'Deep Sea']
    cm = confusion_matrix(y_test, y_pred_ensemble)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names,
                yticklabels=class_names)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix (Soft Voting Ensemble)')
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "confusion_matrix.png")
    plt.close()
    print(f"✅ Saved {ARTIFACTS_DIR / 'confusion_matrix.png'}")
    
    # 6. SHAP (LightGBM)
    print("Generating SHAP Summary...")
    explainer = shap.TreeExplainer(lgb_model)
    shap_values = explainer.shap_values(X_test)
    
    # Multiclass handling for SHAP
    # shap_values is list of arrays [class0, class1, class2]
    # We plot Class 1 (Vegetation) to see what drives it
    target_class = 1 
    if isinstance(shap_values, list):
        print(f"Plotting SHAP for Class {target_class} ({class_names[target_class]})...")
        vals = shap_values[target_class]
    else:
        vals = shap_values

    plt.figure()
    shap.summary_plot(vals, X_test, feature_names=feature_cols, show=False, plot_type="bar")
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "shap_summary.png")
    plt.close()
    print(f"✅ Saved {ARTIFACTS_DIR / 'shap_summary.png'}")

if __name__ == "__main__":
    evaluate()
