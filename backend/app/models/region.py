from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from .base import Base

class Region(Base):
    __tablename__ = "region"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    area_km2 = Column(Float)
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=False)

    # Relationships
    scenes = relationship("Scene", back_populates="region")

    def __repr__(self):
        return f"<Region(name={self.name}, area_km2={self.area_km2})>"
