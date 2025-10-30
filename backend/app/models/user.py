from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.dialects.postgresql import ENUM

user_role = ENUM('viewer', 'analyst', 'admin', name='user_role', create_type=False)

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(user_role, nullable=False, default='viewer')

    teams = relationship("TeamMembership", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
