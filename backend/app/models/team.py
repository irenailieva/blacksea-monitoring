from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User

team_role = ENUM("member", "moderator", "admin", name="team_role", create_type=False)


class Team(Base):
    __tablename__ = "team"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    members: Mapped[list["TeamMembership"]] = relationship(back_populates="team")

    def __repr__(self) -> str:
        return f"<Team(name={self.name})>"


class TeamMembership(Base):
    __tablename__ = "team_membership"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(team_role, nullable=False, default="member")

    user: Mapped["User"] = relationship(back_populates="teams")
    team: Mapped["Team"] = relationship(back_populates="members")

    def __repr__(self) -> str:
        return f"<TeamMembership(user_id={self.user_id}, team_id={self.team_id}, role={self.role})>"
