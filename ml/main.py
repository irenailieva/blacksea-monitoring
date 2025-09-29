import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from model import load_model
from schemas import (
    PredictRequest, PredictResponse,
    PredictBatchRequest, PredictBatchResponse,
    ExplainResponse, HealthResponse
)

load_dotenv()

MODEL_PATH = Path(os.getenv("ML_MODEL_PATH", "artifacts/model.json"))
MODEL_NAME = os.getenv("MODEL_NAME", "LinearMock")
MODEL_VERSION = os.getenv("MODEL_VERSION", "0.1.0")

app = FastAPI(title="BlackSea ML Inference", version=MODEL_VERSION)

# Позволи локалния фронтенд и бекенд (по време на разработка)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Зареждаме модела при старт
try:
    model = load_model(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Неуспешно зареждане на модел от {MODEL_PATH}: {e}")

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        n_features=model.n_features,
    )

@app.post("/infer", response_model=PredictResponse)
def infer(req: PredictRequest):
    try:
        yhat = model.predict_one(req.features)
        return PredictResponse(yhat=yhat)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/infer_batch", response_model=PredictBatchResponse)
def infer_batch(req: PredictBatchRequest):
    try:
        yhat = model.predict_batch(req.batch)
        return PredictBatchResponse(yhat=yhat)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/explain", response_model=ExplainResponse)
def explain(req: PredictRequest):
    try:
        contrib, bias, yhat = model.explain_one(req.features)
        return ExplainResponse(contributions=contrib, bias=bias, yhat=yhat)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
