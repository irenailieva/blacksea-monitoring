from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import MetaData

metadata = MetaData(schema="public")

class Base(DeclarativeBase):
    metadata = metadata

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
