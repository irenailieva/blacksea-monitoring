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

def to_ml_path(p: str) -> str:
    """Translates backend-relative path (/app/ml/...) to ML container path (/app/...)."""
    abs_p = os.path.abspath(p)
    if "/app/ml/" in abs_p:
        return abs_p.replace("/app/ml/", "/app/")
    return p

async def trigger_ml_inference(job_id: int, scene_id_int: int, file_path: str):
    """Calls the ML service and keeps the ETL job status updated throughout."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        # Fetch the string scene_id for consistent filename naming
        from app.crud.scene import scene as crud_scene_local
        db_scene = crud_scene_local.get(db, id=scene_id_int)
        scene_id_str = db_scene.scene_id if db_scene else f"scene_{scene_id_int}"

        # Transition to processing
        db_job = crud_etl_job.etl_job.get(db, id=job_id)
        if db_job:
            payload_update = dict(db_job.payload or {})
            payload_update["progress"] = 10
            crud_etl_job.etl_job.update(
                db, db_obj=db_job,
                obj_in={"status": "processing", "payload": payload_update}
            )

        # Translate path for the ML container which is mounted differently
        ml_file_path = to_ml_path(file_path)
        # Use inference/ subfolder and the string ID prefix
        output_path = to_ml_path(f"/app/ml/data/inference/{scene_id_str}_classification.tif")

        ml_payload = {
            "b2": ml_file_path,
            "b3": ml_file_path,
            "b4": ml_file_path,
            "b8": ml_file_path,
            "scl": ml_file_path,
            "output_path": output_path
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(f"{ML_BASE_URL}/process_scene", json=ml_payload)
            if r.status_code != 200:
                print(f"ML Processing failed for scene {scene_id_str}: {r.status_code} - {r.text}")
            r.raise_for_status()

        print(f"ML Processing completed successfully for scene {scene_id_str}")
        db_job = crud_etl_job.etl_job.get(db, id=job_id)
        if db_job:
            payload_done = dict(db_job.payload or {})
            payload_done["progress"] = 100
            crud_etl_job.etl_job.update(
                db, db_obj=db_job,
                obj_in={"status": "completed", "payload": payload_done,
                        "finished_at": datetime.utcnow()}
            )
    except Exception as e:
        print(f"Failed to trigger ML processing: {e}")
        db_job = crud_etl_job.etl_job.get(db, id=job_id)
        if db_job:
            crud_etl_job.etl_job.update(
                db, db_obj=db_job,
                obj_in={"status": "failed", "finished_at": datetime.utcnow()}
            )
    finally:
        db.close()

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.post("", response_model=schemas.SceneRead, status_code=status.HTTP_201_CREATED)
def create_scene(
    scene_in: schemas.SceneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("analyst", "admin"))
):
    """Създава нова сцена. Изисква researcher или admin роля."""
    return crud_scene.create(db=db, obj_in=scene_in)


@router.get("", response_model=List[schemas.SceneRead])
def read_scenes(
    skip: int = 0,
    limit: int = 100,
    region_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Връща списък от сцени. Изисква автентикация."""
    print(f"[DEBUG] Fetching scenes for user {current_user.username}, region_id={region_id}")
    if region_id:
        res = crud_scene.get_by_region(db=db, region_id=region_id, skip=skip, limit=limit)
    else:
        res = crud_scene.get_multi(db=db, skip=skip, limit=limit)
    print(f"[DEBUG] Returning {len(res)} scenes")
    return res


@router.get("/etl-status", response_model=List[schemas.ETLJobRead])
def get_etl_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the 10 most recent ETL jobs (active + recently finished)."""
    # Always return recent jobs so UI can reflect transitions from pending → completed/failed
    return crud_etl_job.etl_job.get_recent_jobs(db, limit=10)

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
    current_user: User = Depends(require_any_role("analyst", "admin"))
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


@router.post("/upload", response_model=schemas.SceneRead)
async def upload_scene_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("analyst", "admin"))
):
    """Upload a GeoTIFF and queue it for ML inference.
    Re-uploading the same filename is supported — a timestamp suffix
    makes each upload a distinct scene_id so there are no conflicts.
    """
    upload_dir = Path("/app/ml/data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Build a unique stem: original_name + UTC timestamp (seconds precision)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    stem = Path(file.filename).stem
    suffix = Path(file.filename).suffix or ".tif"
    unique_filename = f"{stem}_{ts}{suffix}"
    scene_id_str = f"{stem}_{ts}"          # guaranteed unique per-upload

    file_path = upload_dir / unique_filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    from app.models.region import Region
    region = db.query(Region).first()
    region_id = region.id if region else 1

    scene_in = schemas.SceneCreate(
        scene_id=scene_id_str,
        acquisition_date=datetime.utcnow().date(),
        cloud_cover=None,
        region_id=region_id
    )
    try:
        db_scene = crud_scene.create(db=db, obj_in=scene_in)
    except HTTPException:
        # If somehow still a conflict (edge case), clean up the file
        file_path.unlink(missing_ok=True)
        raise

    job_in = schemas.ETLJobCreate(
        job_type="manual_upload",
        status="pending",
        payload={
            "scene_id": db_scene.id, 
            "scene_id_str": scene_id_str,
            "file_path": str(file_path), 
            "progress": 0
        }
    )
    db_job = crud_etl_job.etl_job.create(db=db, obj_in=job_in.model_dump())

    background_tasks.add_task(trigger_ml_inference, db_job.id, db_scene.id, str(file_path))

    return db_scene

@router.post("/etl-trigger", response_model=schemas.ETLJobRead)
async def trigger_automated_etl(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("analyst", "admin"))
):
    """Triggers the automated Sentinel-2 ETL pipeline."""
    job_in = schemas.ETLJobCreate(
        job_type="sentinel_auto_pipeline",
        status="pending",
        payload={"progress": 0}
    )
    db_job = crud_etl_job.etl_job.create(db=db, obj_in=job_in.model_dump())
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("http://etl:8001/trigger", json={"job_id": db_job.id})
            resp.raise_for_status()
    except Exception as e:
        status_update = schemas.ETLJobUpdate(status="failed")
        db_job = crud_etl_job.etl_job.update(db, db_obj=db_job, obj_in=status_update)
        raise HTTPException(status_code=500, detail=f"Failed to trigger ETL pipeline: {e}")
    
    return db_job


@router.post("/analyze-aoi", response_model=schemas.AoiAnalysisResponse)
async def analyze_aoi(
    request: schemas.AoiAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("analyst", "admin"))
):
    """
    User-driven AOI analysis flow.
    Accepts a bounding box drawn on the map, queries STAC for the best available
    Sentinel-2 scene over that area, runs the full ETL + ML pipeline, and stores
    the classification result in the DB.
    """
    bbox = request.bbox
    aoi_name = request.aoi_name or f"aoi_{bbox[0]:.3f}_{bbox[1]:.3f}"

    job_in = schemas.ETLJobCreate(
        job_type="aoi_analysis",
        status="pending",
        payload={
            "progress": 0,
            "bbox": bbox,
            "aoi_name": aoi_name,
            "cloud_max": request.cloud_max,
        }
    )
    db_job = crud_etl_job.etl_job.create(db=db, obj_in=job_in.model_dump())

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://etl:8001/trigger",
                json={
                    "job_id": db_job.id,
                    "bbox": bbox,
                    "aoi_name": aoi_name,
                    "cloud_max": request.cloud_max,
                }
            )
            resp.raise_for_status()
    except Exception as e:
        crud_etl_job.etl_job.update(db, db_obj=db_job, obj_in={"status": "failed"})
        raise HTTPException(status_code=500, detail=f"Failed to trigger AOI analysis: {e}")

    return schemas.AoiAnalysisResponse(
        job_id=db_job.id,
        status="pending",
        message=f"Analysis started for AOI '{aoi_name}'. Poll /scenes/etl-status for progress."
    )


@router.post("/etl-retry/{job_id}", response_model=schemas.ETLJobRead)
async def retry_etl_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("analyst", "admin"))
):
    """Retry a failed or stuck ETL job.
    - manual_upload: re-runs ML inference on the original file (no re-upload needed).
    - sentinel_auto_pipeline: creates a brand-new pipeline trigger.
    """
    from app.models.etl_job import ETLJob as ETLJobModel
    original = db.query(ETLJobModel).filter(ETLJobModel.id == job_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="ETL job not found")

    if original.status not in ("failed", "pending"):
        raise HTTPException(
            status_code=400,
            detail=f"Only failed or stuck-pending jobs can be retried (current: {original.status})"
        )

    if original.job_type == "manual_upload":
        file_path = (original.payload or {}).get("file_path")
        scene_id  = (original.payload or {}).get("scene_id")
        if not file_path or not Path(file_path).exists():
            raise HTTPException(
                status_code=422,
                detail="Original upload file no longer exists — please re-upload the file."
            )
        # Reset this job to pending and re-queue
        crud_etl_job.etl_job.update(
            db, db_obj=original,
            obj_in={"status": "pending", "finished_at": None,
                    "payload": {**(original.payload or {}), "progress": 0}}
        )
        background_tasks.add_task(trigger_ml_inference, original.id, scene_id, file_path)
        db.refresh(original)
        return original

    else:
        # For sentinel_auto_pipeline: create a fresh job and forward to ETL service
        job_in = schemas.ETLJobCreate(
            job_type="sentinel_auto_pipeline",
            status="pending",
            payload={"progress": 0}
        )
        new_job = crud_etl_job.etl_job.create(db=db, obj_in=job_in.model_dump())
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post("http://etl:8001/trigger", json={"job_id": new_job.id})
                resp.raise_for_status()
        except Exception as e:
            crud_etl_job.etl_job.update(db, db_obj=new_job, obj_in={"status": "failed"})
            raise HTTPException(status_code=500, detail=f"ETL service unreachable: {e}")
        return new_job
