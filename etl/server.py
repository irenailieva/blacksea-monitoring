from fastapi import FastAPI, BackgroundTasks
import uvicorn
from pydantic import BaseModel
from loguru import logger
from typing import List, Optional
import sys
import os

sys.path.append(os.path.dirname(__file__))
from flows.pipeline import run_pipeline

app = FastAPI(title="ETL Trigger API")

class TriggerRequest(BaseModel):
    job_id: int
    bbox: Optional[List[float]] = None   # [minLon, minLat, maxLon, maxLat]
    aoi_name: Optional[str] = None
    cloud_max: Optional[int] = 20

@app.post("/trigger")
def trigger_etl(req: TriggerRequest, bg_tasks: BackgroundTasks):
    logger.info(f"Received ETL trigger job_id={req.job_id} bbox={req.bbox}")
    bg_tasks.add_task(
        run_pipeline,
        job_id=req.job_id,
        bbox=req.bbox,
        aoi_name=req.aoi_name,
        cloud_max=req.cloud_max,
    )
    return {"status": "started", "job_id": req.job_id}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=False)
