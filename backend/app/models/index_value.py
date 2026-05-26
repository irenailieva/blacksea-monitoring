from typing import Optional, TYPE_CHECKING
from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
if TYPE_CHECKING:
    from .scene import Scene
    from .index_type import IndexType
    from .region import Region

class IndexValue(Base):
    """
    ORM модел, съхраняващ изчислените стойности на конкретен индекс (напр. NDVI) 
    за дадена сцена и евентуално за конкретен регион.
    """
    __tablename__ = "index_values"  # Множествено число за консистентност

    # Външни ключове (Foreign keys)
    # ondelete="CASCADE" означава, че ако сцената бъде изтрита, стойността също се изтрива.
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    index_type_id: Mapped[int] = mapped_column(
        ForeignKey("index_types.id", ondelete="CASCADE"), 
        nullable=False
    )
    # Опционално обвързване към регион. Ако регионът се изтрие, това поле става NULL.
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id", ondelete="SET NULL"), nullable=True)

    # Полета за самите стойности (Value columns)
    mean_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # Средна стойност на индекса
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # Минимална стойност
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # Максимална стойност

    # Връзки (Relationships) към родителските обекти
    scene: Mapped["Scene"] = relationship(back_populates="index_values")
    index_type: Mapped["IndexType"] = relationship(back_populates="values")
    region: Mapped[Optional["Region"]] = relationship(back_populates="index_values")

    def __repr__(self) -> str:
        """Стрингова репрезентация, показваща името на индекса и средната стойност."""
        return (
            f"<IndexValue(index={self.index_type.name if self.index_type else None}, "
            f"mean={self.mean_value:.3f if self.mean_value is not None else 'N/A'})>"
        )