from datetime import datetime
from sqlalchemy import MetaData, Column, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, declared_attr

# Define naming convention for constraints
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Shared metadata with naming convention
metadata = MetaData(schema="public", naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """Base class for all ORM models in the project."""
    
    # Use the shared metadata
    metadata = metadata

    # Common columns for all models
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    @declared_attr.directive
    def __mapper_args__(cls) -> dict:
        """Add default ordering by id"""
        if hasattr(cls, 'id'):
            return {"order_by": cls.id}
        return {}
    
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