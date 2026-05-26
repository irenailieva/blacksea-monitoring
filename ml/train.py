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

# ==============================================================================
# ОБУЧЕНИЕ НА МАШИННИ МОДЕЛИ (TRAIN.PY)
# Този скрипт зарежда тренировъчните данни (dataset.csv), изчислява нужните
# спектрални индекси, разделя данните на тренировъчни и тестови, след което 
# обучава три различни модела (Random Forest, XGBoost и LightGBM). 
# Накрая запазва обучените модели на диска и генерира графики.
# ==============================================================================

# Конфигурация
ARTIFACTS_DIR = Path(__file__).parent / "artifacts" # Директория за запазване на моделите
DATA_PATH = Path(__file__).parent / "dataset.csv"   # Път до файла с данните
RANDOM_SEED = 42                                    # За фиксиране на случайността (възпроизводимост)

# Създаване на директорията за артефакти, ако не съществува
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def cleanup_labels(val):
    """
    Функция за изчистване и стандартизиране на етикетите (класовете).
    Гарантира, че моделите се обучават върху вътрешни класове 0, 1, 2.
    0: Пясък / Плитка вода (Абиотични)
    1: Водорасли / Скали (Растителност)
    2: Дълбока вода
    """
    if val == 0: return 0 
    if val == 1: return 1 
    if val == 2: return 2 
    return 2 # Стойност по подразбиране (fallback), ако класът е невалиден

def train():
    """Основна функция за обучение на моделите."""
    print(f"Зареждане на данни от {DATA_PATH}...")
    if not DATA_PATH.exists():
        print(f"Грешка: Файлът с данни не е намерен на адрес {DATA_PATH}.")
        return

    # Зареждане на данните в pandas DataFrame
    df = pd.read_csv(DATA_PATH)
    
    # Предварителна обработка на етикетите (Target Variable)
    if 'class_id' not in df.columns:
        print("Грешка: Колоната 'class_id' липсва в данните.")
        return

    # Прилагане на функцията за изчистване на етикетите
    y = df['class_id'].apply(cleanup_labels).values.astype(int)
    
    # Избор на базовите характеристики (спектрални канали)
    base_cols = ['band_1', 'band_2', 'band_3', 'band_4']
    if not all(col in df.columns for col in base_cols):
        print(f"Грешка: Липсват колонки за каналите. Очаквани: {base_cols}")
        return
    
    # Извличане на каналите (За Sentinel-2: B2=Синьо, B3=Зелено, B4=Червено, B8=NIR)
    blue = df['band_1'].values.astype(float)
    green = df['band_2'].values.astype(float)
    red = df['band_3'].values.astype(float)
    nir = df['band_4'].values.astype(float)
    
    # Проверка дали вегетационните индекси (NDVI, NDWI) са вече изчислени в dataset-а
    if 'ndvi' in df.columns and 'ndwi' in df.columns:
        print("Използване на предварително изчислени индекси от dataset-а.")
        ndvi = df['ndvi'].values.astype(float)
        ndwi = df['ndwi'].values.astype(float)
        # Обединяване на всички колони в една матрица с характеристики X (Форма: [брой_примери, 6])
        X = np.column_stack([blue, green, red, nir, ndvi, ndwi])
    else:
        # Ако липсват, ги изчисляваме в движение чрез помощната функция prepare_features
        print("Изчисляване на индексите в движение...")
        X = prepare_features(blue, green, red, nir)

    print(f"Обучение върху {len(X)} примера с 6 признака: [B2, B3, B4, B8, NDVI, NDWI]...")
    
    # Разделяне на данните на тренировъчни (80%) и тестови (20%)
    # Параметърът stratify=y гарантира, че съотношението на класовете ще е еднакво и в двете множества.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y)
    
    # Имена на класовете за графиките
    class_names = ['Абиотични (Пясък)', 'Растителност', 'Дълбока вода'] # 0, 1, 2

    # 1. Random Forest Classifier
    # Този модел създава множество "дървета на решенията" и осреднява техните резултати.
    # Много добър за предотвратяване на преобучаване (overfitting).
    print("Обучение на Random Forest...")
    rf = RandomForestClassifier(n_estimators=50, max_depth=10, n_jobs=-1, class_weight='balanced', random_state=RANDOM_SEED)
    rf.fit(X_train, y_train)
    rf_acc = accuracy_score(y_test, rf.predict(X_test))
    print(f"Точност на RF: {rf_acc:.4f}")

    # 2. XGBoost (eXtreme Gradient Boosting)
    # Много силен алгоритъм, базиран на последователно надграждане на слаби дървета.
    print("Обучение на XGBoost...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=50, max_depth=6, objective='multi:softmax', num_class=3,
        tree_method="hist", n_jobs=-1, random_state=RANDOM_SEED
    )
    xgb_model.fit(X_train, y_train)
    xgb_acc = accuracy_score(y_test, xgb_model.predict(X_test))
    print(f"Точност на XGB: {xgb_acc:.4f}")

    # 3. LightGBM (Light Gradient Boosting Machine)
    # Подобен на XGBoost, но обикновено по-бърз и по-ефективен при много данни.
    print("Обучение на LightGBM...")
    lgb_model = lgb.LGBMClassifier(
        n_estimators=50, num_leaves=31, objective='multiclass', 
        class_weight='balanced', verbose=-1, random_state=RANDOM_SEED, n_jobs=-1
    )
    lgb_model.fit(X_train, y_train)
    lgb_acc = accuracy_score(y_test, lgb_model.predict(X_test))
    print(f"Точност на LGB: {lgb_acc:.4f}")

    # Запазване на обучените модели на диска
    # Използваме joblib, който е по-ефективен от pickle при големи NumPy масиви.
    print("Запазване на моделите...")
    joblib.dump(rf, ARTIFACTS_DIR / "rf_model.pkl")
    joblib.dump(xgb_model, ARTIFACTS_DIR / "xgb_model.pkl")
    joblib.dump(lgb_model, ARTIFACTS_DIR / "lgb_model.pkl")
    
    print(f"✅ Моделите са запазени в {ARTIFACTS_DIR}")

    # --- Оценка на комбинирания ансамбъл (Soft Voting) ---
    print("\nОценка на Voting Classifier (Soft Voting)...")
    
    # Получаване на вероятностите (probabilities) от всеки отделен модел
    prob1 = rf.predict_proba(X_test)
    prob2 = xgb_model.predict_proba(X_test)
    prob3 = lgb_model.predict_proba(X_test)
    
    # Усредняване на вероятностите
    avg_prob = (prob1 + prob2 + prob3) / 3.0
    
    # Избиране на класа с най-голяма средна вероятност
    y_pred_ensemble = np.argmax(avg_prob, axis=1)
    
    ensemble_acc = accuracy_score(y_test, y_pred_ensemble)
    print(f"🏆 Точност на Soft Voting Ансамбъла: {ensemble_acc:.4f}")

    # --- Визуализации ---
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.metrics import confusion_matrix
    import shap

    print("Генериране на визуализации...")

    # 1. Матрица на грешките (Confusion Matrix) за Ансамбъла
    cm = confusion_matrix(y_test, y_pred_ensemble)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names,
                yticklabels=class_names)
    plt.xlabel('Предсказани класове')
    plt.ylabel('Действителни класове')
    plt.title('Матрица на грешките (Voting Ансамбъл)')
    plt.savefig(ARTIFACTS_DIR / "confusion_matrix.png")
    plt.close()
    print(f"✅ Матрицата на грешките е запазена в {ARTIFACTS_DIR / 'confusion_matrix.png'}")

    # 2. SHAP графики (Използваме LightGBM като представител за значимостта на признаците)
    # TreeExplainer е оптимизиран метод за дървовидни алгоритми като LightGBM.
    explainer = shap.TreeExplainer(lgb_model)
    shap_values = explainer.shap_values(X_test)
    
    # Подготовка за графика тип стълбове (Bar Chart)
    plt.figure()
    
    # Имена на признаците (Зависят от реда в матрицата X)
    feature_names = ['Син (B2)', 'Зелен (B3)', 'Червен (B4)', 'NIR (B8)', 'NDVI', 'NDWI']
    
    # Проверка дали shap_values е списък (при многокласова класификация) или масив (при бинарна)
    if isinstance(shap_values, list):
        # Взимаме клас 1 (Растителност/Водорасли), за да видим какво го дефинира
        vals = shap_values[1]
    else:
        vals = shap_values

    # Чертане на стълбовидна диаграма за глобална значимост на признаците
    shap.summary_plot(vals, X_test, feature_names=feature_names, plot_type="bar", show=False)
    plt.title("Значимост на признаците (SHAP) - Клас: Растителност")
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "shap_summary.png")
    plt.close()
    print(f"✅ SHAP графиката е запазена в {ARTIFACTS_DIR / 'shap_summary.png'}")

if __name__ == "__main__":
    train()
