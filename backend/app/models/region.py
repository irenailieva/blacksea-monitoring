from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.models import Base, Scene

class Region(Base):
    __tablename__ = "region"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255))
    area_km2: Mapped[float | None]
    geometry: Mapped[object] = mapped_column(Geometry("POLYGON", srid=4326), nullable=False)

    # Relationships
    scenes: Mapped[list["Scene"]] = relationship(back_populates="region")

    def __repr__(self) -> str:
        return f"<Region(name={self.name}, area_km2={self.area_km2})>"
