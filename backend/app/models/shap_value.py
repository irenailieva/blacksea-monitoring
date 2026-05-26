from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
if TYPE_CHECKING:
    from .model_run import ModelRun
    from .scene import Scene
    from .index_type import IndexType

class ShapValue(Base):
    """
    ORM модел за съхранение на SHAP (SHapley Additive exPlanations) стойности.
    Осигурява обяснимост на ML моделите, показвайки колко всяка характеристика (feature)
    допринася за крайната класификация.
    """
    __tablename__ = "shap_values"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Външни ключове
    model_run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id", ondelete="CASCADE"), nullable=False)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    index_type_id: Mapped[int] = mapped_column(ForeignKey("index_types.id", ondelete="CASCADE"), nullable=False)

    feature_name: Mapped[str] = mapped_column(String(100), nullable=False) # Име на характеристиката (напр. 'NDWI_mean')
    value: Mapped[float] = mapped_column(Float, nullable=False) # Изчислена SHAP стойност

    # Релации
    model_run: Mapped["ModelRun"] = relationship(back_populates="shap_values")
    scene: Mapped["Scene"] = relationship(back_populates="shap_values")
    index_type: Mapped["IndexType"] = relationship(back_populates="shap_values")

    def __repr__(self) -> str:
        """Стрингова репрезентация за дебъгване."""
        return f"<ShapValue(model_run_id={self.model_run_id}, scene_id={self.scene_id}, feature={self.feature_name})>"
