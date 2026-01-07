"""
CRUD операции за IndexValue модел.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.index_value import IndexValue
from app.models.scene import Scene
from app.models.index_type import IndexType
from app.models.region import Region
from app.schemas import IndexValueCreate, IndexValueUpdate
from .base import CRUDBase


class CRUDIndexValue(CRUDBase[IndexValue]):
    """CRUD операции за IndexValue."""
    
    def create(self, db: Session, *, obj_in: IndexValueCreate) -> IndexValue:
        """Създава нова индексна стойност."""
        # Проверка за съществуваща стойност за същата сцена и тип индекс
        existing = db.query(IndexValue).filter(
            (IndexValue.scene_id == obj_in.scene_id) &
            (IndexValue.index_type_id == obj_in.index_type_id)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="IndexValue for this scene and index_type already exists"
            )
        
        # Проверка за съществуващи обекти
        scene = db.query(Scene).filter(Scene.id == obj_in.scene_id).first()
        if not scene:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scene not found"
            )
        
        index_type = db.query(IndexType).filter(IndexType.id == obj_in.index_type_id).first()
        if not index_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="IndexType not found"
            )
        
        if obj_in.region_id:
            region = db.query(Region).filter(Region.id == obj_in.region_id).first()
            if not region:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Region not found"
                )
        
        # Създаване на индексна стойност
        db_index_value = IndexValue(
            scene_id=obj_in.scene_id,
            index_type_id=obj_in.index_type_id,
            region_id=obj_in.region_id,
            mean_value=obj_in.mean_value,
            min_value=obj_in.min_value,
            max_value=obj_in.max_value
        )
        db.add(db_index_value)
        db.commit()
        db.refresh(db_index_value)
        return db_index_value
    
    def get_by_scene_and_type(
        self,
        db: Session,
        *,
        scene_id: int,
        index_type_id: int
    ) -> Optional[IndexValue]:
        """Връща индексна стойност по сцена и тип индекс."""
        return (
            db.query(IndexValue)
            .filter(
                (IndexValue.scene_id == scene_id) &
                (IndexValue.index_type_id == index_type_id)
            )
            .first()
        )
    
    def get_filtered(
        self,
        db: Session,
        *,
        scene_id: Optional[int] = None,
        index_type_id: Optional[int] = None,
        region_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[IndexValue]:
        """Връща индексни стойности с филтриране."""
        query = db.query(IndexValue)
        
        if scene_id:
            query = query.filter(IndexValue.scene_id == scene_id)
        if index_type_id:
            query = query.filter(IndexValue.index_type_id == index_type_id)
        if region_id:
            query = query.filter(IndexValue.region_id == region_id)
            
        return query.offset(skip).limit(limit).all()
        
    def get_by_scene(
        self,
        db: Session,
        *,
        scene_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[IndexValue]:
        """Връща индексни стойности по сцена (Legacy wrapper)."""
        return self.get_filtered(db, scene_id=scene_id, skip=skip, limit=limit)
    
    def update(
        self,
        db: Session,
        *,
        db_obj: IndexValue,
        obj_in: IndexValueUpdate
    ) -> IndexValue:
        """Обновява индексна стойност."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Проверка за конфликт при обновяване на scene_id или index_type_id
        if "scene_id" in update_data or "index_type_id" in update_data:
            new_scene_id = update_data.get("scene_id", db_obj.scene_id)
            new_index_type_id = update_data.get("index_type_id", db_obj.index_type_id)
            
            existing = db.query(IndexValue).filter(
                (IndexValue.id != db_obj.id) &
                (IndexValue.scene_id == new_scene_id) &
                (IndexValue.index_type_id == new_index_type_id)
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="IndexValue for this scene and index_type already exists"
                )
        
        # Проверка за съществуващи обекти
        if "scene_id" in update_data:
            scene = db.query(Scene).filter(Scene.id == update_data["scene_id"]).first()
            if not scene:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Scene not found"
                )
        
        if "index_type_id" in update_data:
            index_type = db.query(IndexType).filter(IndexType.id == update_data["index_type_id"]).first()
            if not index_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="IndexType not found"
                )
        
        if "region_id" in update_data and update_data["region_id"]:
            region = db.query(Region).filter(Region.id == update_data["region_id"]).first()
            if not region:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Region not found"
                )
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)


index_value = CRUDIndexValue(IndexValue)

