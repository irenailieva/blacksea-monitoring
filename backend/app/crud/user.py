"""
CRUD операции за User модел.
"""
from typing import Optional
from sqlalchemy.orm import Session
# from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password
from .base import CRUDBase

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CRUDUser(CRUDBase[User]):
    """
    CRUD операции, специфични за модела User (Потребител).
    Наследява основните операции от CRUDBase и добавя специфични за автентикацията.
    """
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Създава нов потребител. Първо проверява дали вече не съществува
        потребител със същото име или имейл, след което хешира паролата.
        """
        # Логика за проверка на съществуващ потребител, за да се избегне дублиране.
        existing_user = db.query(User).filter(
            (User.username == obj_in.username) | (User.email == obj_in.email)
        ).first()
        if existing_user:
            # Хвърляне на специфична грешка спрямо това кое поле е дублирано
            if existing_user.username == obj_in.username:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already registered"
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Хеширане на паролата преди запис в базата.
        # Никога не съхраняваме пароли в явен вид (plain-text)!
        hashed_password = hash_password(obj_in.password)
        
        # Създаване на ORM обекта
        db_user = User(
            username=obj_in.username,
            email=obj_in.email,
            password_hash=hashed_password,
            role=obj_in.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Търси и връща потребител по неговото потребителско име."""
        return db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Търси и връща потребител по неговия имейл адрес."""
        return db.query(User).filter(User.email == email).first()
    
    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        """
        Проверява идентификационните данни (credentials). 
        Ако потребителят съществува и паролата е вярна, връща обекта, иначе None.
        """
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        # Проверка чрез функцията verify_password, която сравнява хешове
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    def update(
        self,
        db: Session,
        *,
        db_obj: User,
        obj_in: UserUpdate
    ) -> User:
        """Обновява потребител."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Ако се обновява парола, хешираме я
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))
        
        # Проверка за конфликти при обновяване на username/email
        if "username" in update_data or "email" in update_data:
            existing = db.query(User).filter(
                (User.id != db_obj.id) &
                (
                    (User.username == update_data.get("username", db_obj.username)) |
                    (User.email == update_data.get("email", db_obj.email))
                )
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username or email already exists"
                )
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)


user = CRUDUser(User)

