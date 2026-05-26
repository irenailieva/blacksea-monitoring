from datetime import datetime
from sqlalchemy import MetaData, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Дефиниране на конвенция за наименуване на ограниченията (constraints) в базата данни.
# Това осигурява консистентни имена при създаване на индекси, външни ключове и т.н.
# Улеснява миграциите (напр. с Alembic) при промяна на схемата.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s", # Име за индекс (Index)
    "uq": "uq_%(table_name)s_%(column_0_name)s", # Име за уникално ограничение (Unique constraint)
    "ck": "ck_%(table_name)s_%(constraint_name)s", # Име за проверка (Check constraint)
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s", # Име за външен ключ (Foreign Key)
    "pk": "pk_%(table_name)s" # Име за първичен ключ (Primary Key)
}

# Споделени метаданни, които използват зададената конвенция за наименуване.
metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """
    Базов клас за всички ORM модели в проекта.
    Всички таблици в базата данни ще наследят този клас, което им осигурява
    общи полета (id, created_at, updated_at) и методи.
    """
    
    # Свързване с глобалните метаданни за консистентно именоване
    metadata = metadata

    # Общи колони за всички модели (таблици)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True) # Първичен ключ
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False) # Време на създаване
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False) # Време на последна промяна
    
    def __repr__(self) -> str:
        """
        Метод за стрингова репрезентация на обекта, удобна за дебъгване.
        Показва стойностите на всички колони.
        """
        cols = ", ".join(
            f"{col.name}={getattr(self, col.name)!r}"
            for col in self.__table__.columns
        )
        return f"<{self.__class__.__name__}({cols})>"
    
    @classmethod
    def get_columns(cls) -> list:
        """
        Връща списък с имената на всички колони в таблицата.
        """
        return [col.name for col in cls.__table__.columns]