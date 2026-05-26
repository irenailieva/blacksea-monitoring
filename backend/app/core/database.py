# Импортиране на необходимите модули от SQLAlchemy за създаване на връзка и сесии
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.models.base import Base
from app.models.user import user_role
from app.models.team import team_role

# Извличане на параметрите за връзка от променливите на средата (environment variables).
# Това позволява гъвкава конфигурация без хардкодиране на чувствителни данни.
# При липса на стойности в средата, се използват стойности по подразбиране.
DB_USER = os.getenv("PG_USER", "postgres")
DB_PASS = os.getenv("PG_PASSWORD", "1401")
DB_NAME = os.getenv("PG_DB", "blacksea_monitor")
DB_HOST = os.getenv("PG_HOST", "localhost")
DB_PORT = os.getenv("PG_PORT", "5432")

# Формиране на пълния URL адрес за връзка с PostgreSQL.
# Ако DATABASE_URL не е предварително дефиниран, той се конструира от отделните параметри.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Създаване на SQLAlchemy Engine - основният обект, който комуникира с базата данни.
# echo=True е полезно за разработка, тъй като принтира всички изпълнени SQL заявки в конзолата.
engine = create_engine(DATABASE_URL, echo=True)

# Създаване на клас за сесии (SessionLocal), който ще се използва за създаване на конкретни инстанции.
# autocommit=False и autoflush=False гарантират, че промените трябва да се запазват експлицитно (с db.commit()).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Тази функция ще се използва в FastAPI за достъп до базата чрез Dependency Injection ---
def get_db():
    """
    Създава и освобождава сесия към базата за всеки HTTP request.
    Използва генератор (yield), за да гарантира правилно затваряне на връзката.
    """
    db = SessionLocal()
    try:
        # Предоставя сесията за използване в съответния endpoint
        yield db
    finally:
        # Задължително затваряне на сесията, дори при възникване на грешка,
        # за да се избегне изчерпване на пула от връзки (connection pool).
        db.close()

# Създаване на персонализирани ENUM типове в базата данни преди инициализация на таблиците.
# checkfirst=True проверява дали типът вече съществува, за да предотврати грешки при повторно стартиране.
user_role.create(bind=engine, checkfirst=True)
team_role.create(bind=engine, checkfirst=True)
