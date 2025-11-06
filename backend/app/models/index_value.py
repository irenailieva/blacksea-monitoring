from typing import Optional, TYPE_CHECKING
from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
if TYPE_CHECKING:
    from .scene import Scene
    from .index_type import IndexType
    from .region import Region

class IndexValue(Base):
    """Model representing calculated index values for specific scenes."""
    __tablename__ = "index_values"  # Changed to plural for consistency

    # Foreign keys
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    index_type_id: Mapped[int] = mapped_column(
        ForeignKey("index_types.id", ondelete="CASCADE"), 
        nullable=False
    )
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id", ondelete="SET NULL"), nullable=True)

    # Value columns
    mean_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    scene: Mapped["Scene"] = relationship(back_populates="index_values")
    index_type: Mapped["IndexType"] = relationship(back_populates="values")
    region: Mapped[Optional["Region"]] = relationship(back_populates="index_values")

    def __repr__(self) -> str:
        return (
            f"<IndexValue(index={self.index_type.name if self.index_type else None}, "
            f"mean={self.mean_value:.3f if self.mean_value is not None else 'N/A'})>"
        )