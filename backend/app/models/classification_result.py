from typing import Optional, TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .model_run import ModelRun
    from .scene import Scene
    from .region import Region


class ClassificationResult(Base):
    """
    ORM модел за резултати от класификация.
    Записва изхода от ML моделите (напр. площ на 'vegetation', 'sand', 'water').
    """
    __tablename__ = "classification_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Връзка към изпълнението на модела, което е генерирало този резултат
    model_run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id", ondelete="SET NULL"), nullable=True)
    # Връзка към конкретната сателитна снимка
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    # Връзка към региона (напр. Varna Bay)
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id", ondelete="SET NULL"), nullable=True)

    # Клас от класификацията (напр. 'vegetation')
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    # Увереност (confidence) на модела (между 0 и 1)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Изчислена площ в квадратни метри
    area_m2: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Релации към другите модели
    model_run: Mapped[Optional["ModelRun"]] = relationship(back_populates="classification_results")
    scene: Mapped["Scene"] = relationship(back_populates="classification_results")
    region: Mapped[Optional["Region"]] = relationship(back_populates="classification_results")

    def __repr__(self) -> str:
        """Стрингова репрезентация за дебъгване."""
        return f"<ClassificationResult(scene_id={self.scene_id}, label={self.label}, conf={self.confidence})>"
