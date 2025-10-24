from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app import models

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/")
def list_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users