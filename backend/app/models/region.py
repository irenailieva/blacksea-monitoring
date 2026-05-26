from typing import TYPE_CHECKING

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry # За работа с пространствени данни (GIS) в PostgreSQL/PostGIS

from .base import Base

# Използване на TYPE_CHECKING за избягване на циклични импортирания
if TYPE_CHECKING:
    from .scene import Scene
    from .index_value import IndexValue
    from .classification_result import ClassificationResult


class Region(Base):
    """
    ORM модел за Регион (Area of Interest - AOI).
    Съхранява геометрията на зоната, която се анализира.
    """
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True) # Уникално име на региона
    description: Mapped[str | None] = mapped_column(String(255)) # Опционално описание
    area_km2: Mapped[float | None] # Площ в квадратни километри
    
    # Геометрично поле. Използва PostGIS типа 'Geometry' с POLIGON формат и SRID=4326 (WGS 84 координатна система)
    geometry: Mapped[object] = mapped_column(Geometry("POLYGON", srid=4326), nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="aoi") # Тип на региона (напр. aoi - Area of Interest)

    # Връзки към други таблици (Relationships)
    # Сцени, свързани с този регион
    scenes: Mapped[list["Scene"]] = relationship(back_populates="region")
    # Индексни стойности (NDVI, и др.), изчислени за този регион
    index_values: Mapped[list["IndexValue"]] = relationship(back_populates="region")
    # Резултати от класификация, валидни за този регион
    classification_results: Mapped[list["ClassificationResult"]] = relationship(back_populates="region")

    def __repr__(self) -> str:
        """Стрингова репрезентация за по-лесно проследяване."""
        return f"<Region(name={self.name}, area_km2={self.area_km2})>"
