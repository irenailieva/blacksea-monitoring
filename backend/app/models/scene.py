from typing import TYPE_CHECKING

from sqlalchemy import String, Date, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .region import Region
    from .index_value import IndexValue
    from .scene_file import SceneFile
    from .classification_result import ClassificationResult
    from .shap_value import ShapValue


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scene_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    acquisition_date: Mapped[Date] = mapped_column(Date, nullable=False)
    satellite: Mapped[str] = mapped_column(String(50), nullable=False, default="Sentinel-2")
    cloud_cover: Mapped[float | None] = mapped_column(Float, nullable=True)
    tile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Foreign keys
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    region: Mapped["Region"] = relationship(back_populates="scenes")
    index_values: Mapped[list["IndexValue"]] = relationship(back_populates="scene", cascade="all, delete-orphan")
    files: Mapped[list["SceneFile"]] = relationship(back_populates="scene", cascade="all, delete-orphan")
    classification_results: Mapped[list["ClassificationResult"]] = relationship(back_populates="scene", cascade="all, delete-orphan")
    shap_values: Mapped[list["ShapValue"]] = relationship(back_populates="scene", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Scene(id={self.id}, scene_id='{self.scene_id}', region_id={self.region_id})>"
