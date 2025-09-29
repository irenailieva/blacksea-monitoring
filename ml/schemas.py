from pydantic import BaseModel, Field
from typing import List, Optional

class PredictRequest(BaseModel):
    features: List[float] = Field(..., description="Списък от числови характеристики (x)")

class PredictBatchRequest(BaseModel):
    batch: List[List[float]] = Field(..., description="Списък от вектори (множество наблюдения)")

class PredictResponse(BaseModel):
    yhat: float

class PredictBatchResponse(BaseModel):
    yhat: List[float]

class ExplainResponse(BaseModel):
    contributions: List[float]
    bias: float
    yhat: float

class HealthResponse(BaseModel):
    status: str
    model_name: str
    model_version: str
    n_features: int
