from sqlalchemy.orm import Session
from app import models, schemas
from passlib.hash import bcrypt

def create_user(db: Session, user: schemas.UserCreate):
    """Създава нов потребител, хешира паролата преди запис."""
    hashed_password = bcrypt.hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session):
    return db.query(models.User).all()
