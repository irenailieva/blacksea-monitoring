from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class IndexValue(Base):
    __tablename__ = "index_value"

    id = Column(Integer, primary_key=True)
    scene_id = Column(Integer, ForeignKey("scene.id", ondelete="CASCADE"), nullable=False)
    index_type_id = Column(Integer, ForeignKey("index_type.id", ondelete="CASCADE"), nullable=False)
    mean_value = Column(Float)
    min_value = Column(Float)
    max_value = Column(Float)

    # Relationships
    scene = relationship("Scene", back_populates="index_values")
    index_type = relationship("IndexType", back_populates="values")

    def __repr__(self):
        return f"<IndexValue(index={self.index_type.name}, mean={self.mean_value:.3f})>"
