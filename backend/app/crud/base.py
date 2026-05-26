"""
Базови CRUD операции с транзакции и обработка на грешки.
"""
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    """
    Базов CRUD клас (Create, Read, Update, Delete) с вградени транзакции и обработка на грешки.
    Той се използва като основа, от която наследяват специфичните CRUD класове за всеки модел
    (напр. CRUDUser, CRUDRegion). Този шаблон намалява дублирането на код.
    """
    
    def __init__(self, model: Type[ModelType]):
        # Инициализация с конкретния SQLAlchemy модел (напр. User)
        self.model = model
    
    def create(
        self,
        db: Session,
        *,
        obj_in: dict,
        commit: bool = True
    ) -> ModelType:
        """
        Създава нов запис в базата данни.
        
        Args:
            db: SQLAlchemy сесия (връзка към базата данни)
            obj_in: Речник с данни за създаване на обекта
            commit: Дали да се извърши commit (запазване на промените) веднага.
        
        Returns:
            Създаденият обект, обогатен с ID от базата данни.
        """
        try:
            # Инициализиране на ORM обекта
            db_obj = self.model(**obj_in)
            db.add(db_obj) # Добавяне в текущата сесия
            if commit:
                db.commit() # Физическо запазване в базата
                db.refresh(db_obj) # Опресняване на обекта (зареждане на генерираното ID)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"{self.model.__name__} with these values already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {error_msg}"
            )
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Връща един запис по неговото първично ID.
        Ако записът не е намерен, връща None.
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Връща списък от записи с поддръжка на пагинация (странициране).
        Параметърът `skip` пропуска даден брой записи (offset),
        а `limit` ограничава максималния брой върнати записи.
        """
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in,
        commit: bool = True
    ) -> ModelType:
        """
        Обновява съществуващ запис в базата данни.
        Приема текущия обект от базата (db_obj) и новите данни (obj_in).
        """
        try:
            # Приемане на данни както от Pydantic модели, така и от обикновени речници
            if hasattr(obj_in, 'model_dump'):
                raw = obj_in.model_dump(exclude_unset=True) # За Pydantic v2
            elif hasattr(obj_in, 'dict'):
                raw = obj_in.dict(exclude_unset=True) # За Pydantic v1
            else:
                raw = obj_in
                
            # Игнориране на ключове, чиято стойност е изрично None (ако не искаме да нулираме полета)
            update_data = {k: v for k, v in raw.items() if v is not None}
            
            # Динамично обновяване на атрибутите на ORM обекта
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            if commit:
                db.commit() # Запазване на промените
                db.refresh(db_obj) # Опресняване на обекта
            return db_obj
        except IntegrityError as e:
            # Обработка на грешки при нарушение на уникалността (Unique Constraint)
            db.rollback()
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"{self.model.__name__} with these values already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {error_msg}"
            )
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    def delete(
        self,
        db: Session,
        *,
        id: int,
        commit: bool = True
    ) -> ModelType:
        """
        Изтрива запис по ID.
        
        Args:
            db: SQLAlchemy сесия
            id: ID на записа за изтриване
            commit: Дали да се извърши commit (default: True)
        
        Returns:
            Изтритият обект
        
        Raises:
            HTTPException: Ако записът не съществува
        """
        try:
            db_obj = db.query(self.model).filter(self.model.id == id).first()
            if not db_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} not found"
                )
            db.delete(db_obj)
            if commit:
                db.commit()
            return db_obj
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

