from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .index_value import IndexValue
    from .shap_value import ShapValue

class IndexType(Base):
    """
    ORM модел за видовете индекси (напр. NDVI, NDWI).
    Определя метаданните за индекса (име, описание, формула).
    """
    __tablename__ = "index_types"  # Множествено число за консистентност

    # Полето 'id' се наследява автоматично от базовия клас Base.
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # Уникално име на индекса
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Описание на това какво измерва
    formula: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Математическа формула (напр. (NIR-Red)/(NIR+Red))

    # Връзки (Relationships)
    # Списък от всички изчислени стойности за този тип индекс
    values: Mapped[List["IndexValue"]] = relationship(
        back_populates="index_type",
        cascade="all, delete-orphan"
    )
    shap_values: Mapped[List["ShapValue"]] = relationship(back_populates="index_type", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """Стрингова репрезентация за дебъгване."""
        return f"<IndexType(name='{self.name}')>"