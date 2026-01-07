from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.models.base import Base
from app.models.user import user_role
from app.models.team import team_role

DB_USER = os.getenv("PG_USER", "postgres")
DB_PASS = os.getenv("PG_PASSWORD", "1401")
DB_NAME = os.getenv("PG_DB", "blacksea_monitor")
DB_HOST = os.getenv("PG_HOST", "localhost")
DB_PORT = os.getenv("PG_PORT", "5432")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Тази функция ще се използва в FastAPI за достъп до базата ---
def get_db():
    """Създава и освобождава сесия към базата за всеки HTTP request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ensure custom ENUM types exist before table creation
user_role.create(bind=engine, checkfirst=True)
team_role.create(bind=engine, checkfirst=True)
