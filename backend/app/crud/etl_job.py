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
    """CRUD операции за ETLJob."""
    
    def get_active_jobs(self, db: Session) -> List[ETLJob]:
        """Връща всички активни (pending или running) задачи."""
        return (
            db.query(ETLJob)
            .filter(ETLJob.status.in_(["pending", "running"]))
            .order_by(ETLJob.started_at.desc())
            .all()
        )
    
    def get_recent_jobs(self, db: Session, limit: int = 10) -> List[ETLJob]:
        """Връща последните N задачи."""
        return (
            db.query(ETLJob)
            .order_by(ETLJob.started_at.desc())
            .limit(limit)
            .all()
        )


etl_job = CRUDETLJob(ETLJob)
