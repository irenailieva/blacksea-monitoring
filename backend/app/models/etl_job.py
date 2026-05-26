from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .error_log import ErrorLog


class ETLJob(Base):
    """
    ORM модел за задача за извличане, трансформация и зареждане (ETL).
    Проследява статуса на дълго изпълняващи се фонови задачи,
    като например изтегляне на сателитни данни и изпълнение на ML модели.
    """
    __tablename__ = "etl_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False) # Вид задача (напр. 'download', 'inference')
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending") # Текущ статус
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False) # Начало на задачата
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True) # Край на задачата
    
    # Payload пази параметрите, необходими за изпълнението, в JSON формат
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Връзка с грешките (logs), ако възникнат такива по време на изпълнение
    error_logs: Mapped[list["ErrorLog"]] = relationship(back_populates="etl_job", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """Стрингова репрезентация за дебъгване."""
        return f"<ETLJob(id={self.id}, type={self.job_type}, status={self.status})>"
