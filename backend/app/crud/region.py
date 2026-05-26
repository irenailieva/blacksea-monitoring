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
    """
    CRUD операции за модела Region. 
    Те включват специфична обработка на геопространствени данни (geometry).
    """
    
    def create(self, db: Session, *, obj_in: RegionCreate) -> Region:
        """
        Създава нов регион. Първо проверява за конфликт на името, 
        след което конвертира GeoJSON полигона в PostGIS формат.
        """
        # Проверка дали вече не съществува регион със същото име
        existing = db.query(Region).filter(Region.name == obj_in.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Region with this name already exists"
            )
        
        # Трансформиране на GeoJSON (от HTTP заявката) към геометрия на базата (PostGIS)
        try:
            geom = shape(obj_in.geometry) # Създаване на Shapely обект
            if geom.geom_type != "Polygon":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Geometry must be a Polygon" # Системата поддържа само полигони
                )
            # Конвертиране в WKB (Well-Known Binary) формат за PostGIS (srid=4326 за WGS84)
            geometry = from_shape(geom, srid=4326)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid geometry: {str(e)}"
            )
        
        # Създаване и запазване на региона
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


    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[dict]:
        """
        Връща списък от региони като речници, без да натоварва отговора с тежките 
        геометрични данни (geometry). Подходящо за таблични изгледи в frontend-а.
        """
        # Експлицитно извличане само на скаларните полета (без geometry)
        results = db.query(
            Region.id,
            Region.name,
            Region.description,
            Region.area_km2,
            Region.type,
            Region.created_at,
            Region.updated_at
        ).offset(skip).limit(limit).all()
        
        # Конвертиране на резултатите от базата в списък от речници
        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "area_km2": r.area_km2 if r.area_km2 and r.area_km2 > 0 else 1000.0,
                "type": r.type,
                "created_at": r.created_at,
                "updated_at": r.updated_at
            }
            for r in results
        ]
    
    def get_multi_with_geometry(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[dict]:
        """
        Връща списък от региони, заедно с техните геометрии, конвертирани в GeoJSON.
        Използва се, когато frontend-ът трябва да визуализира полигоните върху картата.
        """
        from geoalchemy2.shape import to_shape
        from sqlalchemy import func
        
        regions = db.query(Region).offset(skip).limit(limit).all()
        
        result = []
        for region in regions:
            try:
                # Преобразуване на PostGIS формата в четим от браузъра GeoJSON
                geom = to_shape(region.geometry)
                geojson = {
                    "type": "Polygon",
                    "coordinates": [list(geom.exterior.coords)]
                }
            except Exception as e:
                print(f"Error converting geometry for region {region.id}: {e}")
                geojson = None
            
            result.append({
                "id": region.id,
                "name": region.name,
                "description": region.description,
                "area_km2": region.area_km2 if region.area_km2 and region.area_km2 > 0 else 1.0,
                "type": region.type,
                "geometry": geojson,
                "created_at": region.created_at,
                "updated_at": region.updated_at
            })
        
        return result

# Инициализация на CRUD обекта за региони
region = CRUDRegion(Region)

