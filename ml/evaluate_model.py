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

# ==============================================================================
# СКРИПТ ЗА ОЦЕНКА НА МОДЕЛИ (EVALUATE MODEL)
# Този скрипт зарежда обучените модели (Random Forest, XGBoost, LightGBM) 
# и оценява тяхната обща производителност чрез "Soft Voting Ensemble" подход.
# Освен това генерира матрица на грешките (Confusion Matrix) и 
# SHAP графики за обяснимост на резултатите от модела.
# ==============================================================================

# Конфигурация на пътищата
BASE_DIR = Path("/app")
DATASET_PATH = BASE_DIR / "dataset.csv"      # Път до файла с данните
ARTIFACTS_DIR = BASE_DIR / "artifacts"       # Директория, където се пазят моделите и графиките

def load_models():
    """
    Функция за зареждане на запазените ML модели от диска.
    Използва joblib за десериализация (четене) на .pkl файловете.
    """
    print("Зареждане на моделите...")
    rf = joblib.load(ARTIFACTS_DIR / "rf_model.pkl")
    xgb = joblib.load(ARTIFACTS_DIR / "xgb_model.pkl")
    lgb = joblib.load(ARTIFACTS_DIR / "lgb_model.pkl")
    return rf, xgb, lgb

def evaluate():
    """
    Основна функция за оценка на моделите.
    """
    # 1. Зареждане на данните
    print(f"Зареждане на данни от {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)
    
    # Проверка дали данните са обогатени с вегетационни индекси (NDVI, NDWI)
    # Ако са налични, използваме и тях като признаци. Ако не - само базовите спектрални канали.
    if 'ndvi' in df.columns and 'ndwi' in df.columns:
        feature_cols = ['band_1', 'band_2', 'band_3', 'band_4', 'ndvi', 'ndwi']
    else:
        # Резервен вариант (Fallback), ако липсват изчислени индекси
        feature_cols = ['band_1', 'band_2', 'band_3', 'band_4']
        
    # X съдържа признаците (характеристиките), y съдържа целевия клас (етикета)
    X = df[feature_cols].values
    y = df['class_id'].values
    
    # 2. Разделяне на данните (Train-Test Split)
    # За да направим честна оценка, разделяме данните отново, като запазваме
    # 20% от тях само за тестване (test_size=0.2). random_state=42 гарантира
    # възпроизводимост на резултатите при всяко стартиране.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Размер на тестовото множество: {len(X_test)} примера")
    
    # 3. Зареждане на обучените модели
    rf, xgb_model, lgb_model = load_models()
    
    # 4. Предсказване чрез "Soft Voting Ensemble"
    # При Soft Voting усредняваме вероятностите, предсказани от всеки отделен модел, 
    # вместо да правим гласуване въз основа на крайния клас (Hard Voting).
    # Това обикновено дава по-точни и стабилни резултати.
    print("Предсказване (Soft Voting)...")
    prob1 = rf.predict_proba(X_test)         # Вероятности от Random Forest
    prob2 = xgb_model.predict_proba(X_test)  # Вероятности от XGBoost
    prob3 = lgb_model.predict_proba(X_test)  # Вероятности от LightGBM
    
    # Усредняване на вероятностите
    avg_prob = (prob1 + prob2 + prob3) / 3.0
    # Крайният клас е този с най-висока средна вероятност (argmax)
    y_pred_ensemble = np.argmax(avg_prob, axis=1)
    
    # Изчисляване на точността (Accuracy)
    acc = accuracy_score(y_test, y_pred_ensemble)
    print(f"🏆 Точност на ансамбъла: {acc:.4f}")
    
    # 5. Генериране на Матрица на грешките (Confusion Matrix)
    # Матрицата на грешките показва колко често моделът е предсказал правилно 
    # всеки клас и къде най-често бърка.
    print("Генериране на Матрица на грешките (Confusion Matrix)...")
    class_names = ['Абиотични (Пясък/Скали)', 'Растителност (Водорасли)', 'Дълбока вода']
    cm = confusion_matrix(y_test, y_pred_ensemble)
    
    # Визуализация на матрицата чрез библиотеката seaborn
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names,
                yticklabels=class_names)
    plt.xlabel('Предсказани класове')
    plt.ylabel('Действителни класове')
    plt.title('Матрица на грешките (Soft Voting Ансамбъл)')
    plt.tight_layout()
    # Запазване на графиката като изображение
    plt.savefig(ARTIFACTS_DIR / "confusion_matrix.png")
    plt.close()
    print(f"✅ Запазена графика: {ARTIFACTS_DIR / 'confusion_matrix.png'}")
    
    # 6. SHAP Анализ на значимостта на признаците (LightGBM)
    # SHAP (SHapley Additive exPlanations) е метод от теорията на игрите
    # за обяснение на предсказанията на ML модели.
    print("Генериране на SHAP Summary графика...")
    explainer = shap.TreeExplainer(lgb_model)
    shap_values = explainer.shap_values(X_test)
    
    # Обработка на SHAP стойности при многокласова класификация
    # shap_values връща списък от масиви [class0, class1, class2]
    # Ние се фокусираме върху Клас 1 (Растителност), за да разберем кои признаци 
    # (напр. NDVI, NDWI) допринасят най-много за идентифицирането на водорасли.
    target_class = 1 
    if isinstance(shap_values, list):
        print(f"Чертане на SHAP графика за Клас {target_class} ({class_names[target_class]})...")
        vals = shap_values[target_class]
    else:
        vals = shap_values

    # Чертане на SHAP Summary plot тип "bar" (стълбовидна диаграма), която показва
    # глобалната значимост на всеки признак.
    plt.figure()
    shap.summary_plot(vals, X_test, feature_names=feature_cols, show=False, plot_type="bar")
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "shap_summary.png")
    plt.close()
    print(f"✅ Запазена графика: {ARTIFACTS_DIR / 'shap_summary.png'}")

if __name__ == "__main__":
    evaluate()
