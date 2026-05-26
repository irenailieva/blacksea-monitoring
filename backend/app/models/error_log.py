from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .etl_job import ETLJob


class ErrorLog(Base):
    """
    ORM модел за записване на грешки (logs).
    Свързан е с ETLJobs, за да се проследяват проблеми при изпълнението на фонови задачи.
    """
    __tablename__ = "error_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Външен ключ към ETL задачата, генерирала грешката
    etl_job_id: Mapped[int] = mapped_column(ForeignKey("etl_jobs.id", ondelete="CASCADE"), nullable=False)

    level: Mapped[str] = mapped_column(String(20), nullable=False, default="ERROR") # Ниво на грешката (ERROR, WARNING)
    message: Mapped[str] = mapped_column(Text, nullable=False) # Кратко съобщение
    stacktrace: Mapped[str | None] = mapped_column(Text, nullable=True) # Пълен stacktrace за дебъгване
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False) # Време на възникване

    etl_job: Mapped["ETLJob"] = relationship(back_populates="error_logs")

    def __repr__(self) -> str:
        """Стрингова репрезентация за дебъгване."""
        return f"<ErrorLog(id={self.id}, etl_job_id={self.etl_job_id}, level={self.level})>"
