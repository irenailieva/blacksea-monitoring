from fastapi import FastAPI, BackgroundTasks
import uvicorn
from pydantic import BaseModel
from loguru import logger
from typing import List, Optional
import sys
import os

sys.path.append(os.path.dirname(__file__))
from flows.pipeline import run_pipeline

# Инициализация на FastAPI приложението с име
app = FastAPI(title="ETL Trigger API")

# Дефиниране на модел за заявка (Request) чрез Pydantic. 
# Това служи за валидация на входните данни при извикване на API-то.
class TriggerRequest(BaseModel):
    job_id: int # Уникален идентификатор на задачата
    bbox: Optional[List[float]] = None   # Ограничаваща рамка [minLon, minLat, maxLon, maxLat]
    aoi_name: Optional[str] = None       # Име на зоната на интерес (Area of Interest)
    display_name: Optional[str] = None   # Име за показване в потребителския интерфейс
    cloud_max: Optional[int] = 20        # Максимално допустимо облачно покритие (по подразбиране 20%)

# Дефиниране на POST маршрут (endpoint) за стартиране на ETL процеса
@app.post("/trigger")
def trigger_etl(req: TriggerRequest, bg_tasks: BackgroundTasks):
    # Логване на информация за получената заявка
    logger.info(f"Received ETL trigger job_id={req.job_id} bbox={req.bbox}")
    
    # Добавяне на задачата към фоновите задачи (BackgroundTasks).
    # Това позволява на API-то да върне отговор веднага, докато процесът работи асинхронно.
    bg_tasks.add_task(
        run_pipeline,
        job_id=req.job_id,
        bbox=req.bbox,
        aoi_name=req.aoi_name,
        display_name=req.display_name,
        cloud_max=req.cloud_max,
    )
    
    # Връщане на статус отговор към клиента
    return {"status": "started", "job_id": req.job_id}

# Дефиниране на GET маршрут за проверка на здравето (health check) на сървъра.
# Използва се за мониторинг дали услугата работи правилно.
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Точка за влизане в програмата. Ако скриптът се стартира директно (не като модул),
# сървърът ще се стартира на порт 8001, слушайки всички интерфейси (0.0.0.0).
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=False)
