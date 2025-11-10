"""
CRUD операции за IndexType модел.
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.index_type import IndexType
from app.schemas import IndexTypeCreate, IndexTypeUpdate
from .base import CRUDBase


class CRUDIndexType(CRUDBase[IndexType]):
    """CRUD операции за IndexType."""
    
    def create(self, db: Session, *, obj_in: IndexTypeCreate) -> IndexType:
        """Създава нов тип индекс."""
        # Проверка за съществуващ тип индекс с това име
        existing = db.query(IndexType).filter(IndexType.name == obj_in.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="IndexType with this name already exists"
            )
        
        # Създаване на тип индекс
        db_index_type = IndexType(
            name=obj_in.name,
            description=obj_in.description,
            formula=obj_in.formula
        )
        db.add(db_index_type)
        db.commit()
        db.refresh(db_index_type)
        return db_index_type
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[IndexType]:
        """Връща тип индекс по име."""
        return db.query(IndexType).filter(IndexType.name == name).first()
    
    def update(
        self,
        db: Session,
        *,
        db_obj: IndexType,
        obj_in: IndexTypeUpdate
    ) -> IndexType:
        """Обновява тип индекс."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Проверка за конфликт при обновяване на име
        if "name" in update_data:
            existing = db.query(IndexType).filter(
                (IndexType.id != db_obj.id) &
                (IndexType.name == update_data["name"])
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="IndexType with this name already exists"
                )
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)


index_type = CRUDIndexType(IndexType)

