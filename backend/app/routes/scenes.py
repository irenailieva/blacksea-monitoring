import shutil
import httpx
import os
from datetime import datetime
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_any_role
from app.models.user import User
from app import schemas
from app.crud import scene as crud_scene
from app.crud import etl_job as crud_etl_job

ML_BASE_URL = os.getenv("ML_BASE_URL", "http://ml:8500")

async def trigger_ml_inference(job_id: int, scene_id: int, file_path: str):
    """Вика ML услугата за обработка на сцената."""
    try:
        payload = {
            "b2": file_path,
            "b3": file_path,
            "b4": file_path,
            "b8": file_path,
            "scl": file_path,
            "output_path": f"/app/ml/data/classified_{scene_id}.tif"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{ML_BASE_URL}/process_scene", json=payload)
            r.raise_for_status()
            
        print(f"ML Processing triggered successfully for scene {scene_id}")
    except Exception as e:
        print(f"Failed to trigger ML processing: {e}")

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.post("/", response_model=schemas.SceneRead, status_code=status.HTTP_201_CREATED)
def create_scene(
    scene_in: schemas.SceneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """Създава нова сцена. Изисква researcher или admin роля."""
    return crud_scene.create(db=db, obj_in=scene_in)


@router.get("/", response_model=List[schemas.SceneRead])
def read_scenes(
    skip: int = 0,
    limit: int = 100,
    region_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Връща списък от сцени. Изисква автентикация."""
    if region_id:
        return crud_scene.get_by_region(db=db, region_id=region_id, skip=skip, limit=limit)
    return crud_scene.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{scene_id}", response_model=schemas.SceneRead)
def read_scene(
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Връща сцена по ID. Изисква автентикация."""
    db_scene = crud_scene.get(db=db, id=scene_id)
    if not db_scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    return db_scene


@router.put("/{scene_id}", response_model=schemas.SceneRead)
def update_scene(
    scene_id: int,
    scene_in: schemas.SceneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """Обновява сцена. Изисква researcher или admin роля."""
    db_scene = crud_scene.get(db=db, id=scene_id)
    if not db_scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    return crud_scene.update(db=db, db_obj=db_scene, obj_in=scene_in)


@router.delete("/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scene(
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("admin"))
):
    """Изтрива сцена. Изисква admin роля."""
    db_scene = crud_scene.get(db=db, id=scene_id)
    if not db_scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    crud_scene.delete(db=db, id=scene_id)
    return None


@router.get("/etl-status", response_model=List[schemas.ETLJobRead])
def get_etl_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Връща статуса на активните ETL задачи."""
    # За демо цели, ако няма нищо в базата, връщаме малко мок данни
    jobs = crud_etl_job.etl_job.get_active_jobs(db)
    if not jobs:
        # Return empty list or some mock for demo if needed
        # But for now, let's return whatever is in the DB
        return crud_etl_job.etl_job.get_recent_jobs(db, limit=5)
    return jobs

@router.post("/upload", response_model=schemas.SceneRead)
async def upload_scene_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """Качва нов GeoTIFF и създава запис за сцена със статус 'pending'."""
    # Ensure the directory exists
    upload_dir = Path("/app/ml/data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create scene record
    scene_in = schemas.SceneCreate(
        sentinel_id=file.filename.split('.')[0],
        acquired_at=datetime.utcnow().isoformat(),
        cloud_coverage=0.0,
        etl_status="processing"
    )
    db_scene = crud_scene.create(db=db, obj_in=scene_in)
    
    # Create an ETL job record
    job_in = schemas.ETLJobCreate(
        job_type="manual_upload",
        status="processing",
        payload={"scene_id": db_scene.id, "file_path": str(file_path)}
    )
    db_job = crud_etl_job.etl_job.create(db=db, obj_in=job_in)
    
    # Trigger inference in background
    background_tasks.add_task(trigger_ml_inference, db_job.id, db_scene.id, str(file_path))
    
    return db_scene

@router.post("/etl-trigger", response_model=schemas.ETLJobRead)
async def trigger_automated_etl(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """Triggers the automated Sentinel-2 ETL pipeline."""
    job_in = schemas.ETLJobCreate(
        job_type="sentinel_auto_pipeline",
        status="pending",
        payload={"progress": 0}
    )
    db_job = crud_etl_job.etl_job.create(db=db, obj_in=job_in)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("http://etl:8001/trigger", json={"job_id": db_job.id})
            resp.raise_for_status()
    except Exception as e:
        status_update = schemas.ETLJobUpdate(status="failed")
        db_job = crud_etl_job.etl_job.update(db, db_obj=db_job, obj_in=status_update)
        raise HTTPException(status_code=500, detail=f"Failed to trigger ETL pipeline: {e}")
    
    return db_job
