"""
API routes за Region ресурс.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_any_role
from app.models.user import User
from app import schemas
from app.crud import region as crud_region

router = APIRouter(prefix="/regions", tags=["regions"])


@router.post("/", response_model=schemas.RegionRead, status_code=status.HTTP_201_CREATED)
def create_region(
    region_in: schemas.RegionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """Създава нов регион. Изисква researcher или admin роля."""
    return crud_region.create(db=db, obj_in=region_in)


@router.get("/", response_model=List[schemas.RegionRead])
def read_regions(
    skip: int = 0,
    limit: int = 100,
    with_geometry: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Връща списък от региони. Изисква автентикация."""
    if with_geometry:
        return crud_region.get_multi_with_geometry(db=db, skip=skip, limit=limit)
    return crud_region.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{region_id}", response_model=schemas.RegionRead)
def read_region(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Връща регион по ID. Изисква автентикация."""
    db_region = crud_region.get(db=db, id=region_id)
    if not db_region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    return db_region


@router.put("/{region_id}", response_model=schemas.RegionRead)
def update_region(
    region_id: int,
    region_in: schemas.RegionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """Обновява регион. Изисква researcher или admin роля."""
    db_region = crud_region.get(db=db, id=region_id)
    if not db_region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    return crud_region.update(db=db, db_obj=db_region, obj_in=region_in)


@router.delete("/{region_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_region(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("admin"))
):
    """Изтрива регион. Изисква admin роля."""
    db_region = crud_region.get(db=db, id=region_id)
    if not db_region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    crud_region.delete(db=db, id=region_id)
    return None

