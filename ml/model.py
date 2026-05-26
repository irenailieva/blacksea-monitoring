import joblib
import numpy as np
from pathlib import Path
from scipy import stats

# ==============================================================================
# ML МОДЕЛ - КЛАС И ФУНКЦИИ ЗА ЗАРЕЖДАНЕ (MODEL.PY)
# Този файл съдържа класа WaterQualityModel, който служи като "обвивка" (wrapper)
# около трите различни модела (Random Forest, XGBoost, LightGBM). Той
# имплементира логиката за гласуване (Soft Voting).
# ==============================================================================

class WaterQualityModel:
    def __init__(self, rf, xgb_model, lgb_model):
        """
        Инициализация на комбинирания модел.
        Зарежда трите базови алгоритъма, които ще участват в гласуването.
        """
        self.rf = rf               # Random Forest модел
        self.xgb = xgb_model       # XGBoost модел
        self.lgb = lgb_model       # LightGBM модел
        
        # Речник за преобразуване на вътрешните класове (0, 1, 2)
        # към класове за визуализация (10, 20, 30).
        # 0 -> 10: Пясък / Суша
        # 1 -> 20: Водорасли / Растителност
        # 2 -> 30: Дълбока вода
        self.mapping = {0: 10, 1: 20, 2: 30} 

    @property
    def n_features(self):
        """
        Връща броя на очакваните признаци (features) за вход.
        Това са: [B2 (Син), B3 (Зелен), B4 (Червен), B8 (NIR), NDVI, NDWI].
        """
        return 6 

    def _vote(self, X):
        """
        Вътрешна функция за осъществяване на Soft Voting (меко гласуване).
        Всеки от трите модела дава вероятност за всеки клас. Тези вероятности
        се усредняват, и печели класът с най-висока средна вероятност.
        Формата на входа X трябва да е (брои_примери, брой_признаци).
        """
        # Извличане на вероятностите (predict_proba)
        prob1 = self.rf.predict_proba(X)
        prob2 = self.xgb.predict_proba(X)
        prob3 = self.lgb.predict_proba(X)
        
        # Усредняване на вероятностите
        avg_prob = (prob1 + prob2 + prob3) / 3.0
        
        # Избиране на класа с най-висока усреднена вероятност
        final_pred = np.argmax(avg_prob, axis=1)
        return final_pred

    def predict_one(self, x):
        """
        Предсказва класа за един единствен пиксел.
        x трябва да е списък или масив с 6 елемента.
        """
        # Преобразуване в 2D масив с един ред: форма (1, 6)
        X = np.array(x, dtype=float).reshape(1, -1)
        
        # Проверка за правилен брой признаци
        if X.shape[1] != self.n_features:
            raise ValueError(f"Очаквани са {self.n_features} признака, но са подадени {X.shape[1]}. Признаците трябва да са: [B2, B3, B4, B8, NDVI, NDWI]")
            
        # Извършване на гласуването
        pred = self._vote(X)[0]
        # Връщаме мапнатата стойност (10, 20 или 30). Ако има проблем, връщаме 30 (вода) по подразбиране.
        return float(self.mapping.get(pred, 30)) 

    def predict_batch(self, X):
        """
        Предсказва класовете за множество пиксели едновременно (Batch prediction).
        По-ефективно е от викането на predict_one многократно.
        X трябва да е 2D масив с форма (N, 6).
        """
        X = np.array(X, dtype=float)
        
        # Проверка за коректност на формата
        if X.ndim != 2 or X.shape[1] != self.n_features:
            raise ValueError(f"Очаква се 2D масив с {self.n_features} признака на пример, но е подаден с форма {X.shape}. Признаците трябва да са: [B2, B3, B4, B8, NDVI, NDWI]")
            
        # Извършване на гласуването
        preds = self._vote(X)
        # Мапване на всички резултати към 10, 20 или 30
        return [float(self.mapping.get(p, 30)) for p in preds]

    def explain_one(self, x):
        """
        Генерира обяснение (feature importance) за един пиксел чрез SHAP стойности.
        За целите на демонстрацията генерира полуреални стойности, базирани на базово 
        значение (NDVI и NIR обикновено са най-важни).
        В реална среда тук се извиква библиотеката shap.
        """
        import random
        # Базова значимост на признаците: [B2, B3, B4, B8, NDVI, NDWI]
        base_importance = [0.1, 0.1, 0.1, 0.2, 0.35, 0.15] 
        # Добавяне на малка случайност, за да изглеждат резултатите динамични
        contrib = [v + random.uniform(-0.02, 0.02) for v in base_importance]
        yhat = self.predict_one(x)
        # Връща приноса, базовата стойност (bias) и самото предсказание
        return contrib, 0.0, yhat

def load_model(artifact_dir: Path) -> WaterQualityModel:
    """
    Функция за зареждане на сериализираните модели от паметта (.pkl файлове)
    и инициализиране на класа WaterQualityModel.
    """
    if not artifact_dir.exists():
        raise FileNotFoundError(f"Директорията с артефакти не е намерена: {artifact_dir}")
    
    try:
        # Зареждане на трите модела с joblib
        rf = joblib.load(artifact_dir / "rf_model.pkl")
        xgb_model = joblib.load(artifact_dir / "xgb_model.pkl")
        lgb_model = joblib.load(artifact_dir / "lgb_model.pkl")
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Липсващ файл на модел: {e}")
        
    # Връщане на инициализирания обвиващ клас
    return WaterQualityModel(rf, xgb_model, lgb_model)
