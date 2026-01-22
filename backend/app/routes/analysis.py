from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.get("/vegetation-trend")
def get_vegetation_trend(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Mock data aggregated from DB in a real app
    # For now, return realistic mock data that satisfies the component
    return [
        { "date": "2023-06", "vegetation": 3100, "sand": 900 },
        { "date": "2023-07", "vegetation": 3400, "sand": 850 },
        { "date": "2023-08", "vegetation": 3200, "sand": 800 },
        { "date": "2023-09", "vegetation": 2900, "sand": 1000 },
        { "date": "2023-10", "vegetation": 2600, "sand": 1200 },
        { "date": "2023-11", "vegetation": 2200, "sand": 1400 },
        { "date": "2023-12", "vegetation": 1800, "sand": 1600 },
    ]

@router.get("/shap-values")
def get_shap_values(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # In a real app, this would call the ML /explain endpoint for the latest scene in the region
    return [
        { "feature": "NDVI", "value": 0.52 },
        { "feature": "NDWI", "value": 0.38 },
        { "feature": "NIR (B8)", "value": 0.25 },
        { "feature": "Green (B3)", "value": 0.12 },
        { "feature": "Blue (B2)", "value": -0.08 },
        { "feature": "Red (B4)", "value": -0.15 },
    ]
