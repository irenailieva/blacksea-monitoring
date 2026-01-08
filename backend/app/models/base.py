from datetime import datetime
from sqlalchemy import MetaData, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Define naming convention for constraints
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Shared metadata with naming convention
# Shared metadata with naming convention
metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """Base class for all ORM models in the project."""
    
    # Use the shared metadata
    metadata = metadata

    # Common columns for all models
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        """Clean debug-friendly string representation for all models."""
        cols = ", ".join(
            f"{col.name}={getattr(self, col.name)!r}"
            for col in self.__table__.columns
        )
        return f"<{self.__class__.__name__}({cols})>"
    
    @classmethod
    def get_columns(cls) -> list:
        """Get list of model column names."""
        return [col.name for col in cls.__table__.columns]