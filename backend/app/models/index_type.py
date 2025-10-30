from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from .base import Base

class IndexType(Base):
    __tablename__ = "index_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # e.g., "NDVI", "NDWI"
    description = Column(Text)
    formula = Column(String(255))  # optional, for documentation

    # Relationships
    values = relationship("IndexValue", back_populates="index_type")

    def __repr__(self):
        return f"<IndexType(name={self.name})>"
