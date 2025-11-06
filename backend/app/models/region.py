from typing import TYPE_CHECKING

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from .base import Base
if TYPE_CHECKING:
    from .scene import Scene
    from .index_value import IndexValue
    from .classification_result import ClassificationResult


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255))
    area_km2: Mapped[float | None]
    geometry: Mapped[object] = mapped_column(Geometry("POLYGON", srid=4326), nullable=False)

    # Relationships
    scenes: Mapped[list["Scene"]] = relationship(back_populates="region")
    index_values: Mapped[list["IndexValue"]] = relationship(back_populates="region")
    classification_results: Mapped[list["ClassificationResult"]] = relationship(back_populates="region")

    def __repr__(self) -> str:
        return f"<Region(name={self.name}, area_km2={self.area_km2})>"
