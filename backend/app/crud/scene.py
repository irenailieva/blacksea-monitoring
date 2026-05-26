"""
CRUD операции за Scene модел.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.scene import Scene
from app.models.region import Region
from app.schemas import SceneCreate, SceneUpdate
from .base import CRUDBase


class CRUDScene(CRUDBase[Scene]):
    """
    CRUD операции за модела Scene (Сателитна сцена).
    """
    
    def create(self, db: Session, *, obj_in: SceneCreate) -> Scene:
        """
        Създава нова сцена. Включва проверки за валидност на региона 
        и уникалност на идентификатора на сцената (scene_id).
        """
        # Проверка дали вече съществува сцена с този идентификатор,
        # за да се избегне дублиране на данни при многократно изтегляне.
        existing = db.query(Scene).filter(Scene.scene_id == obj_in.scene_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Scene with this scene_id already exists"
            )
        
        # Проверка дали посоченият регион съществува в базата данни.
        # Всяка сцена трябва да е обвързана с валиден регион.
        region = db.query(Region).filter(Region.id == obj_in.region_id).first()
        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Region not found"
            )
        
        # Инициализиране на ORM обекта
        db_scene = Scene(
            scene_id=obj_in.scene_id,
            acquisition_date=obj_in.acquisition_date,
            satellite=obj_in.satellite,
            cloud_cover=obj_in.cloud_cover,
            tile=obj_in.tile,
            path=obj_in.path,
            region_id=obj_in.region_id
        )
        db.add(db_scene)
        db.commit()
        db.refresh(db_scene)
        return db_scene
    
    def get_by_scene_id(self, db: Session, *, scene_id: str) -> Optional[Scene]:
        """Търси и връща сцена по нейния уникален стринг идентификатор (scene_id)."""
        return db.query(Scene).filter(Scene.scene_id == scene_id).first()
    
    def get_by_region(
        self,
        db: Session,
        *,
        region_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Scene]:
        """
        Връща списък със сцени, които принадлежат на конкретен регион.
        Поддържа пагинация чрез параметрите skip и limit.
        """
        return (
            db.query(Scene)
            .filter(Scene.region_id == region_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def update(
        self,
        db: Session,
        *,
        db_obj: Scene,
        obj_in: SceneUpdate
    ) -> Scene:
        """Обновява сцена."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Проверка за конфликт при обновяване на scene_id
        if "scene_id" in update_data:
            existing = db.query(Scene).filter(
                (Scene.id != db_obj.id) &
                (Scene.scene_id == update_data["scene_id"])
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Scene with this scene_id already exists"
                )
        
        # Проверка за съществуващ регион ако се обновява region_id
        if "region_id" in update_data:
            region = db.query(Region).filter(Region.id == update_data["region_id"]).first()
            if not region:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Region not found"
                )
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)


scene = CRUDScene(Scene)

