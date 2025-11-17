"""
API routes за IndexType ресурс.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_any_role
from app.models.user import User
from app import schemas
from app.crud import index_type as crud_index_type

router = APIRouter(prefix="/index-types", tags=["index-types"])


@router.post("/", response_model=schemas.IndexTypeRead, status_code=status.HTTP_201_CREATED)
def create_index_type(
    index_type_in: schemas.IndexTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """Създава нов тип индекс. Изисква researcher или admin роля."""
    return crud_index_type.create(db=db, obj_in=index_type_in)


@router.get("/", response_model=List[schemas.IndexTypeRead])
def read_index_types(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Връща списък от типове индекси. Изисква автентикация."""
    return crud_index_type.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{index_type_id}", response_model=schemas.IndexTypeRead)
def read_index_type(
    index_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Връща тип индекс по ID. Изисква автентикация."""
    db_index_type = crud_index_type.get(db=db, id=index_type_id)
    if not db_index_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IndexType not found"
        )
    return db_index_type


@router.put("/{index_type_id}", response_model=schemas.IndexTypeRead)
def update_index_type(
    index_type_id: int,
    index_type_in: schemas.IndexTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """Обновява тип индекс. Изисква researcher или admin роля."""
    db_index_type = crud_index_type.get(db=db, id=index_type_id)
    if not db_index_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IndexType not found"
        )
    return crud_index_type.update(db=db, db_obj=db_index_type, obj_in=index_type_in)


@router.delete("/{index_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_index_type(
    index_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("admin"))
):
    """Изтрива тип индекс. Изисква admin роля."""
    db_index_type = crud_index_type.get(db=db, id=index_type_id)
    if not db_index_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IndexType not found"
        )
    crud_index_type.delete(db=db, id=index_type_id)
    return None

