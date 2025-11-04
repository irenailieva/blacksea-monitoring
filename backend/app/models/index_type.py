from typing import List, Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, Scene, IndexValue


class IndexType(Base):
    """Model representing different types of indices that can be calculated."""
    __tablename__ = "index_types"  # Changed to plural for consistency

    # No need to define id as it's inherited from Base
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    formula: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    values: Mapped[List["IndexValue"]] = relationship(
        back_populates="index_type",
        cascade="all, delete-orphan"
    )
    scenes: Mapped[List["Scene"]] = relationship(
        back_populates="index_type"
    )

    def __repr__(self) -> str:
        return f"<IndexType(name='{self.name}')>"