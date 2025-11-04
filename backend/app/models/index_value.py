from typing import Optional
from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, Scene, IndexType

class IndexValue(Base):
    """Model representing calculated index values for specific scenes."""
    __tablename__ = "index_values"  # Changed to plural for consistency

    # Foreign keys
    scene_id: Mapped[int] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"), 
        nullable=False
    )
    index_type_id: Mapped[int] = mapped_column(
        ForeignKey("index_types.id", ondelete="CASCADE"), 
        nullable=False
    )

    # Value columns
    mean_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    scene: Mapped["Scene"] = relationship(back_populates="index_value")
    index_type: Mapped["IndexType"] = relationship(back_populates="values")

    def __repr__(self) -> str:
        return (
            f"<IndexValue(index={self.index_type.name if self.index_type else None}, "
            f"mean={self.mean_value:.3f if self.mean_value is not None else 'N/A'})>"
        )