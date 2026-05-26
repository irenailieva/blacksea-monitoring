from pydantic import BaseModel, Field
from typing import List, Optional

# ==============================================================================
# СХЕМИ ЗА ВАЛИДАЦИЯ (SCHEMAS.PY)
# Този файл използва библиотеката Pydantic за дефиниране на структурите от данни,
# които API-то очаква да получи (Requests) и които връща като отговор (Responses).
# Това гарантира, че данните са винаги в правилния формат (напр. списъци от числа).
# ==============================================================================

class PredictRequest(BaseModel):
    """
    Схема за заявка за предсказване на единичен пиксел.
    Очаква списък от 6 числа (B2, B3, B4, B8, NDVI, NDWI).
    """
    features: List[float] = Field(..., description="Списък от числови характеристики (x)")

class PredictBatchRequest(BaseModel):
    """
    Схема за заявка за масово предсказване (Batch prediction).
    Очаква списък от списъци (матрица), където всеки вътрешен списък е отделен пиксел.
    """
    batch: List[List[float]] = Field(..., description="Списък от вектори (множество наблюдения)")

class PredictResponse(BaseModel):
    """
    Схема за отговора при предсказване на единичен пиксел.
    Връща едно число (клас: 10, 20 или 30).
    """
    yhat: float

class PredictBatchResponse(BaseModel):
    """
    Схема за отговора при масово предсказване.
    Връща списък от числа (класовете за всички подадени пиксели).
    """
    yhat: List[float]

class ExplainResponse(BaseModel):
    """
    Схема за отговора на заявка за обяснимост на модела (SHAP).
    """
    contributions: List[float] # Приносът на всяка характеристика
    bias: float                # Базовата стойност (изместване)
    yhat: float                # Предсказаният клас

class HealthResponse(BaseModel):
    """
    Схема за отговора на Health Check (проверка на състоянието).
    """
    status: str          # "ok" или "error"
    model_name: str      # Име на модела
    model_version: str   # Версия на модела
    n_features: int      # Очакван брой характеристики (6)
