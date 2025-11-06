from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    etl_job_id: Mapped[int] = mapped_column(ForeignKey("etl_jobs.id", ondelete="CASCADE"), nullable=False)

    level: Mapped[str] = mapped_column(String(20), nullable=False, default="ERROR")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    stacktrace: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    etl_job: Mapped["ETLJob"] = relationship(back_populates="error_logs")

    def __repr__(self) -> str:
        return f"<ErrorLog(id={self.id}, etl_job_id={self.etl_job_id}, level={self.level})>"


