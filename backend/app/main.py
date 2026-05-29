import os
import httpx
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Импортиране на рутерите (routers) за отделните модули на приложението
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

# Зареждане на променливите от средата (environment variables) от .env файл
load_dotenv()

# Основен URL за връзка с Machine Learning (ML) услугата (микросървис)
ML_BASE_URL = os.getenv("ML_BASE_URL", "http://localhost:8500")

# Разрешени източници (origins) за CORS (Cross-Origin Resource Sharing)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

# Праг в минути, след който неактивна ETL задача (job) се счита за неуспешна (stale/failed)
STALE_THRESHOLD_MINUTES = 10

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление на жизнения цикъл на FastAPI приложението (startup/shutdown).
    Използва се за инициализиране на базата данни и почистване на изостанали процеси.
    """
    # Създаване на всички таблици в базата данни, ако те вече не съществуват.
    Base.metadata.create_all(bind=engine)
    
    # Първоначално зареждане (seeding) на регионите в базата данни.
    try:
        from seed_regions import seed_regions
        seed_regions()
    except Exception as e:
        print(f"[Lifespan] Error seeding regions: {e}")

    # Проверка и добавяне на колони, ако липсват (idempotent schema migrations).
    from sqlalchemy import text
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE scenes ADD COLUMN IF NOT EXISTS display_name VARCHAR(100);"))
            conn.execute(text("ALTER TABLE classification_results ADD COLUMN IF NOT EXISTS area_m2 DOUBLE PRECISION;"))
        print("[Lifespan] Schema migrations applied (display_name, classification_results.area_m2).")
    except Exception as e:
        print(f"[Lifespan] Error applying schema migrations: {e}")


    # Почистване на стари ETL (Extract, Transform, Load) задачи, които са останали "висящи" при евентуален срив.
    db = SessionLocal()
    try:
        # Изчисляване на времевия праг за стари задачи.
        cutoff = datetime.utcnow() - timedelta(minutes=STALE_THRESHOLD_MINUTES)
        
        # Заявка за намиране на всички задачи в процес на изпълнение или чакащи, които са започнали преди прага.
        stale = (
            db.query(ETLJob)
            .filter(ETLJob.status.in_(["pending", "processing", "running"]))
            .filter(ETLJob.started_at < cutoff)
            .all()
        )
        
        # Ако има такива задачи, те се маркират като неуспешни (failed).
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
        # Винаги затваряме връзката към базата данни, за да не задръстваме connection pool-а.
        db.close()

    # Този yield предава контрола на FastAPI да стартира същинското приложение.
    yield  # application runs here

# Инициализация на основното FastAPI приложение.
app = FastAPI(title="BlackSea Monitoring API", lifespan=lifespan)

# Създаване на таблиците (ако още не съществуват) - прави се и в lifespan, но тук е като резерва
Base.metadata.create_all(bind=engine)

# Конфигурация на CORS (Cross-Origin Resource Sharing) middleware.
# Позволява на frontend приложението (напр. React) да прави заявки към този backend API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Временно се позволяват всички източници за целите на дебъгване
    allow_credentials=True, # Позволява изпращането на cookies (напр. за аутентикация)
    allow_methods=["*"], # Позволява всички HTTP методи (GET, POST, PUT, DELETE)
    allow_headers=["*"], # Позволява всички HTTP headers
)

# Дефиниране на директория за статични файлове, която се използва от ML моделите.
# Това позволява директен достъп до данни през API-то (например чрез /data/...).
ML_DATA_DIR = "/app/ml/data"
if os.path.exists(ML_DATA_DIR):
    # Монтиране на директорията като статични файлове
    app.mount("/data", StaticFiles(directory=ML_DATA_DIR), name="data")
    print(f"✅ Mounted {ML_DATA_DIR} to /data")
else:
    print(f"⚠️ Warning: {ML_DATA_DIR} does not exist. /data mount failed.")

############## 
# Основен маршрут (Root endpoint) за бърза проверка дали сървърът работи
##############
@app.get("/")
def root():
    return {"message":"Backend API is running! :)"}

##############
# Маршрут за проверка на състоянието (Health Check), често използван от Docker/Kubernetes
##############
@app.get("/health")
def health_check():
    return {"status": "ok"}

##########################
# Прогнозиране (Извикване на ML модел)
##########################
@app.post("/predict")
async def predict(features: list[float] = Body(..., embed=True)):
    """
    Прокси маршрут към ML микросървиса (endpoint /infer).
    Приема списък от признаци (features) и връща предсказание от модела.
    """
    try:
        # Асинхронно изпращане на POST заявка към ML услугата с timeout от 10 секунди
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{ML_BASE_URL}/infer", json={"features": features})
        # Проверка за грешка при отговора (HTTP status >= 400)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        # В случай на грешка в мрежата или в ML услугата, се връща HTTP 502 Bad Gateway
        raise HTTPException(status_code=502, detail=f"ML service error: {str(e)}")

########################################
# Прогнозиране + Обяснение (Извикване на ML модел и SHAP)
########################################
@app.post("/predict_explain")
async def predict_explain(features: list[float] = Body(..., embed=True)):
    """
    Прокси маршрут към ML микросървиса (endpoint /explain).
    Освен предсказание, връща и обяснение на модела (напр. чрез SHAP стойности).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{ML_BASE_URL}/explain", json={"features": features})
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"ML service error: {str(e)}")

#########################################
# ВКЛЮЧВАНЕ НА РУТЕРИТЕ (ROUTERS) В ПРИЛОЖЕНИЕТО
# Всеки рутер отговаря за определена група от функционалности (напр. потребители, региони).
#########################################
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(regions_router.router)
app.include_router(scenes_router.router)
app.include_router(index_types_router.router)
app.include_router(index_values_router.router)
app.include_router(teams_router.router)
app.include_router(analysis_router.router)