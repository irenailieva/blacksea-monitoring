from typing import Optional, TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .model_run import ModelRun
    from .scene import Scene
    from .region import Region


class ClassificationResult(Base):
    __tablename__ = "classification_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id", ondelete="SET NULL"), nullable=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id", ondelete="SET NULL"), nullable=True)

    label: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    model_run: Mapped[Optional["ModelRun"]] = relationship(back_populates="classification_results")
    scene: Mapped["Scene"] = relationship(back_populates="classification_results")
    region: Mapped[Optional["Region"]] = relationship(back_populates="classification_results")

    def __repr__(self) -> str:
        return f"<ClassificationResult(scene_id={self.scene_id}, label={self.label}, conf={self.confidence})>"


