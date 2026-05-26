from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
if TYPE_CHECKING:
    from .user import User

class WebhookIntegration(Base):
    """
    ORM модел за Webhook интеграции.
    Позволява на потребителите да получават HTTP POST заявки към техни сървъри
    при възникване на определени събития в системата (напр. нова сцена).
    """
    __tablename__ = "webhook_integrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    provider: Mapped[str] = mapped_column(String(50), nullable=False) # Доставчик (напр. 'slack', 'discord', 'custom')
    endpoint_url: Mapped[str] = mapped_column(String(255), nullable=False) # URL, към който се изпраща заявката
    secret: Mapped[str | None] = mapped_column(String(255), nullable=True) # Споделена тайна за HMAC подписване (сигурност)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # Дали webhook-ът е активен

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        """Стрингова репрезентация за дебъгване."""
        return f"<WebhookIntegration(user_id={self.user_id}, provider={self.provider})>"
