from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
if TYPE_CHECKING:
    from .user import User


class Notification(Base):
    """
    ORM модел за системни известия към потребителите.
    Използва се за информиране при завършени ETL задачи или промени в данните.
    """
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Външен ключ към потребителя, за когото е предназначено известието
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(120), nullable=False) # Заглавие
    message: Mapped[str] = mapped_column(String(500), nullable=False) # Текст на известието
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) # Флаг дали е прочетено

    user: Mapped["User"] = relationship(back_populates="notifications")

    def __repr__(self) -> str:
        """Стрингова репрезентация за дебъгване."""
        return f"<Notification(user_id={self.user_id}, title={self.title})>"
