import os
import httpx
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.routes import auth as auth_router
from app.routes import users as users_router
from app.routes import regions as regions_router
from app.routes import scenes as scenes_router
from app.routes import index_types as index_types_router
from app.routes import index_values as index_values_router
from app.routes import teams as teams_router
from app.routes import analysis as analysis_router

from app.core.database import Base, engine, SessionLocal
from app.models.etl_job import ETLJob

load_dotenv()

ML_BASE_URL = os.getenv("ML_BASE_URL", "http://localhost:8500")
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

STALE_THRESHOLD_MINUTES = 10  # jobs stuck longer than this get marked failed

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables and resolve any stale ETL jobs left over from a crash."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=STALE_THRESHOLD_MINUTES)
        stale = (
            db.query(ETLJob)
            .filter(ETLJob.status.in_(["pending", "processing", "running"]))
            .filter(ETLJob.started_at < cutoff)
            .all()
        )
        if stale:
            for job in stale:
                job.status = "failed"
                job.finished_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
            db.commit()
            print(f"[Watchdog] Marked {len(stale)} stale job(s) as failed on startup.")
        else:
            print("[Watchdog] No stale jobs found.")
    except Exception as e:
        print(f"[Watchdog] Error resolving stale jobs: {e}")
    finally:
        db.close()

    yield  # application runs here

app = FastAPI(title="BlackSea Monitoring API", lifespan=lifespan)

# Създаване на таблиците (ако още не съществуват)
Base.metadata.create_all(bind=engine)

#Allows front-end requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount ML data directory as static files
# Docker maps host ./ml to /app/ml (which maps to backend container's /app/ml if volumes set correctly)
# OR backend maps ./ml to /app/ml directly.
# Let's check docker-compose.yml:
# backend: volumes: - ./backend:/app
# AND it needs access to ml data.
# The previous analysis showed backend container does NOT have ml volume mounted!
# We found a bug in the docker-compose.yml check earlier?
# Wait, let me check docker-compose.yml again in my thought process or re-read it.
# Re-reading step 9 output:
#   backend:
#     volumes:
#       - ./backend:/app
# It does NOT have ./ml mounted.
# So even if I mount StaticFiles, the data isn't there!
# I need to fix docker-compose.yml first to mount ./ml into backend.

# BUT for now I will add the code to main.py, assuming the volume will be there.
# I will also have to fix docker-compose.yml.

# Let's use a robust path.
# Mount ML data directory as static files
# Docker maps host ./ml to /app/ml
ML_DATA_DIR = "/app/ml/data"
if os.path.exists(ML_DATA_DIR):
    app.mount("/data", StaticFiles(directory=ML_DATA_DIR), name="data")
    print(f"✅ Mounted {ML_DATA_DIR} to /data")
else:
    print(f"⚠️ Warning: {ML_DATA_DIR} does not exist. /data mount failed.")

############## 
# Initial Test
##############
@app.get("/")
def root():
    return {"message":"Backend API is running! :)"}

##############
# Health Check
##############
@app.get("/health")
def health_check():
    return {"status": "ok"}

##########################
# Prediction (Call to ML)
##########################
@app.post("/predict")
async def predict(features: list[float] = Body(..., embed=True)):
    """
    Proxy към ML /infer. Пример body:
    { "features": [1.0, 2.0, 3.0] }
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{ML_BASE_URL}/infer", json={"features": features})
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"ML service error: {str(e)}")

########################################
# Prediction + Explanation (Call to ML)
########################################
@app.post("/predict_explain")
async def predict_explain(features: list[float] = Body(..., embed=True)):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{ML_BASE_URL}/explain", json={"features": features})
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"ML service error: {str(e)}")

#########################################
# INCLUDING ROUTERS IN APP
#########################################
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(regions_router.router)
app.include_router(scenes_router.router)
app.include_router(index_types_router.router)
app.include_router(index_values_router.router)
app.include_router(teams_router.router)
app.include_router(analysis_router.router)