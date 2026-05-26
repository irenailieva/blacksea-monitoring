from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

# TYPE_CHECKING предотвратява циклични зависимости (circular imports).
# Тези модули се импортират само по време на проверка на типовете (mypy/IDE),
# но не и по време на изпълнение на кода.
if TYPE_CHECKING:
    from .team import TeamMembership
    from .notification import Notification

# Дефиниране на изброим тип (ENUM) за потребителски роли в PostgreSQL.
user_role = ENUM("admin", "researcher", "viewer", name="user_role")


class User(Base):
    """
    ORM модел, представляващ потребител в системата.
    Съдържа идентификационни данни, парола и роля.
    """
    __tablename__ = "user"

    # Основни полета за автентикация
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # Уникално потребителско име
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False) # Уникален имейл адрес
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False) # Хеширана парола (никога в явен текст)
    role: Mapped[str] = mapped_column(user_role, nullable=False, default="viewer") # Роля по подразбиране е 'viewer'

    # Връзки (Relationships) към други таблици
    # Един потребител може да участва в множество екипи (teams)
    teams: Mapped[list["TeamMembership"]] = relationship(back_populates="user")
    # Един потребител може да има множество известия (notifications)
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        """Стрингова репрезентация за дебъгване."""
        return f"<User(username={self.username}, role={self.role})>"
