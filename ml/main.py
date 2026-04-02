import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from model import load_model, WaterQualityModel
from schemas import (
    PredictRequest, PredictResponse,
    PredictBatchRequest, PredictBatchResponse,
    ExplainResponse, HealthResponse
)
from image_processor import process_scene

load_dotenv()

# Config
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "artifacts"))
MODEL_NAME = os.getenv("MODEL_NAME", "BlackSea_Ensemble_v1")
MODEL_VERSION = os.getenv("MODEL_VERSION", "1.0.0")

app = FastAPI(title="BlackSea ML Inference", version=MODEL_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
model: WaterQualityModel = None

@app.on_event("startup")
def startup_event():
    global model
    try:
        model = load_model(ARTIFACTS_DIR)
        print(f"✅ Model loaded successfully from {ARTIFACTS_DIR}")
    except Exception as e:
        print(f"⚠️ Failed to load model: {e}")
        # We don't raise here to allow the app to start, but health check will show error
        model = None

@app.get("/health", response_model=HealthResponse)
def health():
    status = "ok" if model else "error"
    return HealthResponse(
        status=status,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        n_features=model.n_features if model else -1,
    )

@app.post("/infer", response_model=PredictResponse)
def infer(req: PredictRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        yhat = model.predict_one(req.features)
        return PredictResponse(yhat=yhat)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/infer_batch", response_model=PredictBatchResponse)
def infer_batch(req: PredictBatchRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        yhat = model.predict_batch(req.batch)
        return PredictBatchResponse(yhat=yhat)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/explain", response_model=ExplainResponse)
def explain(req: PredictRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        contrib, bias, yhat = model.explain_one(req.features)
        return ExplainResponse(contributions=contrib, bias=bias, yhat=yhat)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ProcessSceneRequest(BaseModel):
    b2: str
    b3: str
    b4: str
    b8: str
    scl: str
    output_path: str

@app.post("/process_scene")
def process_scene_endpoint(req: ProcessSceneRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")

    band_paths = {
        'b2': req.b2, 'b3': req.b3, 'b4': req.b4, 'b8': req.b8, 'scl': req.scl
    }

    # Ensure output directory exists before rasterio tries to write
    from pathlib import Path
    output_dir = Path(req.output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        process_scene(band_paths, req.output_path, model)
        return {"status": "success", "output_path": req.output_path}
    except Exception as e:
        import traceback
        detail = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=detail)
