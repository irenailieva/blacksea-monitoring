from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .shap_value import ShapValue
    from .classification_result import ClassificationResult


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="completed")
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    shap_values: Mapped[list["ShapValue"]] = relationship(back_populates="model_run", cascade="all, delete-orphan")
    classification_results: Mapped[list["ClassificationResult"]] = relationship(back_populates="model_run", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ModelRun(id={self.id}, model_name={self.model_name}, status={self.status})>"


