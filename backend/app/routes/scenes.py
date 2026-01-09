"""
API routes за Scene ресурс.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_any_role
from app.models.user import User
from app import schemas
from app.crud import scene as crud_scene
from app.crud import etl_job as crud_etl_job

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

