"""
CRUD операции за Region модел с геопространствени данни.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from fastapi import HTTPException, status

from app.models.region import Region
from app.schemas import RegionCreate, RegionUpdate
from .base import CRUDBase


class CRUDRegion(CRUDBase[Region]):
    """CRUD операции за Region с геопространствени данни."""
    
    def create(self, db: Session, *, obj_in: RegionCreate) -> Region:
        """Създава нов регион с геопространствени данни."""
        # Проверка за съществуващ регион с това име
        existing = db.query(Region).filter(Region.name == obj_in.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Region with this name already exists"
            )
        
        # Конвертиране на GeoJSON geometry към PostGIS Geometry
        try:
            geom = shape(obj_in.geometry)
            if geom.geom_type != "Polygon":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Geometry must be a Polygon"
                )
            geometry = from_shape(geom, srid=4326)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid geometry: {str(e)}"
            )
        
        # Създаване на регион
        db_region = Region(
            name=obj_in.name,
            description=obj_in.description,
            area_km2=obj_in.area_km2,
            geometry=geometry
        )
        db.add(db_region)
        db.commit()
        db.refresh(db_region)
        return db_region
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[Region]:
        """Връща регион по име."""
        return db.query(Region).filter(Region.name == name).first()
    
    def update(
        self,
        db: Session,
        *,
        db_obj: Region,
        obj_in: RegionUpdate
    ) -> Region:
        """Обновява регион."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Проверка за конфликт при обновяване на име
        if "name" in update_data:
            existing = db.query(Region).filter(
                (Region.id != db_obj.id) &
                (Region.name == update_data["name"])
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Region with this name already exists"
                )
        
        # Конвертиране на geometry ако е предоставена
        if "geometry" in update_data:
            try:
                geom = shape(update_data["geometry"])
                if geom.geom_type != "Polygon":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Geometry must be a Polygon"
                    )
                update_data["geometry"] = from_shape(geom, srid=4326)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid geometry: {str(e)}"
                )
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)


region = CRUDRegion(Region)

