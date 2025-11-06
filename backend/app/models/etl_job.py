from datetime import datetime
from typing import Any

from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ETLJob(Base):
    __tablename__ = "etl_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    error_logs: Mapped[list["ErrorLog"]] = relationship(back_populates="etl_job", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ETLJob(id={self.id}, type={self.job_type}, status={self.status})>"


