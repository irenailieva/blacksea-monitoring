from typing import TYPE_CHECKING

from sqlalchemy import String, Date, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

# Избягване на циклични импортирания по време на изпълнение
if TYPE_CHECKING:
    from .region import Region
    from .index_value import IndexValue
    from .scene_file import SceneFile
    from .classification_result import ClassificationResult
    from .shap_value import ShapValue


class Scene(Base):
    """
    ORM модел за сателитна сцена.
    Всяка сцена представлява конкретна снимка (запис), направена в даден момент
    от даден сателит над определен регион.
    """
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scene_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False) # Уникален идентификатор от доставчика на данни
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True) # Име за показване на потребителите
    acquisition_date: Mapped[Date] = mapped_column(Date, nullable=False) # Дата на заснемане
    satellite: Mapped[str] = mapped_column(String(50), nullable=False, default="Sentinel-2") # Сателит (напр. Sentinel-2)
    cloud_cover: Mapped[float | None] = mapped_column(Float, nullable=True) # Процент облачно покритие
    tile: Mapped[str | None] = mapped_column(String(20), nullable=True) # Идентификатор на "плочката" (tile)
    path: Mapped[str | None] = mapped_column(String(255), nullable=True) # Път към суровите данни на диска

    # Външен ключ (Foreign Key) към региона, към който спада снимката.
    # ondelete="RESTRICT" предотвратява изтриването на регион, ако има сцени в него.
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False)

    # Връзки (Relationships)
    region: Mapped["Region"] = relationship(back_populates="scenes")
    
    # Cascade="all, delete-orphan" означава, че ако сцената бъде изтрита,
    # свързаните към нея стойности също ще бъдат автоматично изтрити.
    index_values: Mapped[list["IndexValue"]] = relationship(back_populates="scene", cascade="all, delete-orphan")
    files: Mapped[list["SceneFile"]] = relationship(back_populates="scene", cascade="all, delete-orphan")
    classification_results: Mapped[list["ClassificationResult"]] = relationship(back_populates="scene", cascade="all, delete-orphan")
    shap_values: Mapped[list["ShapValue"]] = relationship(back_populates="scene", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """Репрезентация за дебъгване."""
        return f"<Scene(id={self.id}, scene_id='{self.scene_id}', region_id={self.region_id})>"
