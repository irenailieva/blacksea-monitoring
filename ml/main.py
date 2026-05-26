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

# ==============================================================================
# ОСНОВЕН СЪРВЪР (MAIN.PY) - FASTAPI
# Този скрипт стартира уеб сървър, който предоставя REST API за връзка с ML модела.
# Frontend-ът комуникира с тези endpoints, за да генерира карти и предсказания.
# ==============================================================================

# Зареждане на променливи от средата (обикновено от .env файл)
load_dotenv()

# Конфигурация на сървъра
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "artifacts"))
MODEL_NAME = os.getenv("MODEL_NAME", "BlackSea_Ensemble_v1")
MODEL_VERSION = os.getenv("MODEL_VERSION", "1.0.0")

# Създаване на FastAPI приложението
app = FastAPI(title="BlackSea ML Inference", version=MODEL_VERSION)

# Настройка на CORS (Cross-Origin Resource Sharing)
# Позволява на frontend-а (напр. работещ на localhost:5173) да прави заявки към този сървър
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобална променлива, която ще държи заредения модел в паметта
model: WaterQualityModel = None

@app.on_event("startup")
def startup_event():
    """
    Тази функция се изпълнява автоматично при стартиране на сървъра.
    Опитва се да зареди модела от диска. Ако не го намери, автоматично
    стартира скрипта за обучение (train.py).
    """
    global model
    try:
        model = load_model(ARTIFACTS_DIR)
        print(f"✅ Моделът е зареден успешно от {ARTIFACTS_DIR}")
    except Exception as e:
        print(f"⚠️ Неуспешно зареждане на модела: {e}. Опит за обучение...")
        try:
            import subprocess
            # Стартиране на процеса по обучение
            subprocess.run(["python", "train.py"], check=True)
            # След успешно обучение, зареждаме новия модел
            model = load_model(ARTIFACTS_DIR)
            print(f"✅ Моделът е обучен и зареден успешно от {ARTIFACTS_DIR}")
        except Exception as inner_e:
            print(f"⚠️ Критична грешка при обучение и зареждане на модела: {inner_e}")
            model = None

@app.get("/health", response_model=HealthResponse)
def health():
    """
    Прост endpoint за проверка на състоянието на сървъра (Health check).
    Връща информация дали моделът е зареден успешно.
    """
    status = "ok" if model else "error"
    return HealthResponse(
        status=status,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        n_features=model.n_features if model else -1,
    )

@app.post("/infer", response_model=PredictResponse)
def infer(req: PredictRequest):
    """
    Endpoint за предсказване на единична точка (пиксел).
    Приема спектралните стойности и връща предсказания клас.
    """
    if not model:
        raise HTTPException(status_code=503, detail="Моделът не е зареден")
    
    try:
        yhat = model.predict_one(req.features)
        return PredictResponse(yhat=yhat)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/infer_batch", response_model=PredictBatchResponse)
def infer_batch(req: PredictBatchRequest):
    """
    Endpoint за масово предсказване на много точки едновременно.
    Използва се за по-висока производителност.
    """
    if not model:
        raise HTTPException(status_code=503, detail="Моделът не е зареден")

    try:
        yhat = model.predict_batch(req.batch)
        return PredictBatchResponse(yhat=yhat)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/explain", response_model=ExplainResponse)
def explain(req: PredictRequest):
    """
    Endpoint за обяснимост на резултатите (Explainability) чрез SHAP.
    Връща приноса на всяка характеристика (band) за крайното решение.
    """
    if not model:
        raise HTTPException(status_code=503, detail="Моделът не е зареден")

    try:
        contrib, bias, yhat = model.explain_one(req.features)
        return ExplainResponse(contributions=contrib, bias=bias, yhat=yhat)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Схема за заявка за обработка на цяла сателитна сцена
class ProcessSceneRequest(BaseModel):
    b2: str
    b3: str
    b4: str
    b8: str
    scl: str
    output_path: str

@app.post("/process_scene")
def process_scene_endpoint(req: ProcessSceneRequest):
    """
    Основен endpoint за обработка на цели сателитни сцени.
    Приема пътища до отделните канали и генерира крайна TIF/PNG карта.
    """
    if not model:
        raise HTTPException(status_code=503, detail="Моделът не е зареден")

    # Събиране на пътищата в речник
    band_paths = {
        'b2': req.b2, 'b3': req.b3, 'b4': req.b4, 'b8': req.b8, 'scl': req.scl
    }

    # Подсигуряване, че изходната директория съществува
    from pathlib import Path
    output_dir = Path(req.output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Извикване на функцията за обработка на изображението
        stats = process_scene(band_paths, req.output_path, model)
        return {"status": "success", "output_path": req.output_path, "stats": stats}
    except Exception as e:
        # При грешка връщаме детайлен stack trace
        import traceback
        detail = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=detail)
