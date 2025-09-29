import os
import httpx
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import auth as auth_router

load_dotenv()

ML_BASE_URL = os.getenv("ML_BASE_URL", "http://localhost:8500")
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(title="BlackSea Monitoring API")

# In-memory store (временно вместо БД)
app.state.users_store = {}  # ключ: username → стойност: dict_за_потребителя

#Allows front-end requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins, #Vite dev server address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# INCLUDING AUTH ROUTER IN APP ROUTER SET
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])