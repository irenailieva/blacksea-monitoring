from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, text
from app.db import Base
import enum

# --- Enum за ролите на потребителите ---
class UserRole(str, enum.Enum):
    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"

# --- SQLAlchemy модел за таблицата "user" ---
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(Enum(UserRole), nullable=False, server_default="viewer")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
