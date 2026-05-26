"""
CRUD операции за ETLJob модел.
"""
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.etl_job import ETLJob
from app.schemas import ETLJobCreate, ETLJobUpdate
from .base import CRUDBase


class CRUDETLJob(CRUDBase[ETLJob]):
    """
    CRUD операции за модела ETLJob (задачи във фонов режим).
    """
    
    def get_active_jobs(self, db: Session) -> List[ETLJob]:
        """
        Връща всички активни задачи, които в момента се изпълняват или чакат.
        Това е полезно за показване на индикатори за прогрес (progress bars) във frontend-а.
        """
        return (
            db.query(ETLJob)
            .filter(ETLJob.status.in_(["pending", "running", "processing"]))
            .order_by(ETLJob.started_at.desc()) # Подреждане от най-новите към най-старите
            .all()
        )
    
    def get_recent_jobs(self, db: Session, limit: int = 10) -> List[ETLJob]:
        """
        Връща последните N на брой задачи (включително приключили и неуспешни).
        Използва се за история на изпълненията (logs/history).
        """
        return (
            db.query(ETLJob)
            .order_by(ETLJob.started_at.desc())
            .limit(limit)
            .all()
        )


etl_job = CRUDETLJob(ETLJob)
