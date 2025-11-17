"""
API routes за IndexValue ресурс.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_any_role
from app.models.user import User
from app import schemas
from app.crud import index_value as crud_index_value

router = APIRouter(prefix="/index-values", tags=["index-values"])


@router.post("/", response_model=schemas.IndexValueRead, status_code=status.HTTP_201_CREATED)
def create_index_value(
    index_value_in: schemas.IndexValueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """Създава нова индексна стойност. Изисква researcher или admin роля."""
    return crud_index_value.create(db=db, obj_in=index_value_in)


@router.get("/", response_model=List[schemas.IndexValueRead])
def read_index_values(
    skip: int = 0,
    limit: int = 100,
    scene_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Връща списък от индексни стойности. Изисква автентикация."""
    if scene_id:
        return crud_index_value.get_by_scene(db=db, scene_id=scene_id, skip=skip, limit=limit)
    return crud_index_value.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{index_value_id}", response_model=schemas.IndexValueRead)
def read_index_value(
    index_value_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Връща индексна стойност по ID. Изисква автентикация."""
    db_index_value = crud_index_value.get(db=db, id=index_value_id)
    if not db_index_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IndexValue not found"
        )
    return db_index_value


@router.put("/{index_value_id}", response_model=schemas.IndexValueRead)
def update_index_value(
    index_value_id: int,
    index_value_in: schemas.IndexValueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """Обновява индексна стойност. Изисква researcher или admin роля."""
    db_index_value = crud_index_value.get(db=db, id=index_value_id)
    if not db_index_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IndexValue not found"
        )
    return crud_index_value.update(db=db, db_obj=db_index_value, obj_in=index_value_in)


@router.delete("/{index_value_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_index_value(
    index_value_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("admin"))
):
    """Изтрива индексна стойност. Изисква admin роля."""
    db_index_value = crud_index_value.get(db=db, id=index_value_id)
    if not db_index_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IndexValue not found"
        )
    crud_index_value.delete(db=db, id=index_value_id)
    return None

