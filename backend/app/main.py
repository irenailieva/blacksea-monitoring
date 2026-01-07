import os
import httpx
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

from app.core.database import Base, engine

load_dotenv()

ML_BASE_URL = os.getenv("ML_BASE_URL", "http://localhost:8500")
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(title="BlackSea Monitoring API")

# Създаване на таблиците (ако още не съществуват)
Base.metadata.create_all(bind=engine)

#Allows front-end requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins, #Vite dev server address
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
ML_DATA_DIR = "/app/ml"
if os.path.exists(ML_DATA_DIR):
    app.mount("/data", StaticFiles(directory=ML_DATA_DIR), name="data")
    print(f"Mounted {ML_DATA_DIR} to /data")
else:
    print(f"WARNING: ML data directory not found at {ML_DATA_DIR}. Static files will not be served.")

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