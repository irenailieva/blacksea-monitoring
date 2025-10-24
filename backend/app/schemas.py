from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum

# --- Enum (дублиран за Pydantic, не може да ползваме SQLAlchemy enum директно) ---
class UserRole(str, Enum):
    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"

# --- Модел за създаване на потребител ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.viewer

# --- Модел за четене на потребител (response) ---
class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    class Config:
        orm_mode = True  # Позволява работа директно с SQLAlchemy обекти
