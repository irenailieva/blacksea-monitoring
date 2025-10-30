from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.dialects.postgresql import ENUM

team_role = ENUM('member', 'moderator', 'admin', name='team_role', create_type=False)

class Team(Base):
    __tablename__ = "team"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    members = relationship("TeamMembership", back_populates="team")

class TeamMembership(Base):
    __tablename__ = "team_membership"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("team.id"), nullable=False)
    role = Column(team_role, nullable=False, default='member')

    user = relationship("User", back_populates="teams")
    team = relationship("Team", back_populates="members")
