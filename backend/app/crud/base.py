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
    """Базов CRUD клас с транзакции и обработка на грешки."""
    
    def __init__(self, model: Type[ModelType]):
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
            db: SQLAlchemy сесия
            obj_in: Речник с данни за създаване
            commit: Дали да се извърши commit (default: True)
        
        Returns:
            Създаденият обект
        
        Raises:
            HTTPException: При constraint violation или друга DB грешка
        """
        try:
            db_obj = self.model(**obj_in)
            db.add(db_obj)
            if commit:
                db.commit()
                db.refresh(db_obj)
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
        """Връща запис по ID."""
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Връща списък от записи с pagination."""
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: dict,
        commit: bool = True
    ) -> ModelType:
        """
        Обновява съществуващ запис.
        
        Args:
            db: SQLAlchemy сесия
            db_obj: Обект за обновяване
            obj_in: Речник с данни за обновяване (само непразни стойности)
            commit: Дали да се извърши commit (default: True)
        
        Returns:
            Обновеният обект
        
        Raises:
            HTTPException: При constraint violation или друга DB грешка
        """
        try:
            # Обновяваме само непразните стойности
            update_data = {k: v for k, v in obj_in.items() if v is not None}
            
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            if commit:
                db.commit()
                db.refresh(db_obj)
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

