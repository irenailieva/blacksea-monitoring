from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/analysis", tags=["analysis"])

from sqlalchemy import func
from app.models.classification_result import ClassificationResult
from app.models.shap_value import ShapValue
from app.models.scene import Scene

@router.get("/vegetation-trend")
def get_vegetation_trend(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Query real data: Group by acquisition_date for the selected region
    from sqlalchemy import case
    results = db.query(
        Scene.acquisition_date,
        func.sum(case([(ClassificationResult.label == 'vegetation', ClassificationResult.area_m2)], else_=0)).label('vegetation'),
        func.sum(case([(ClassificationResult.label == 'sand', ClassificationResult.area_m2)], else_=0)).label('sand')
    ).join(ClassificationResult, Scene.id == ClassificationResult.scene_id)\
     .filter(Scene.region_id == region_id)\
     .group_by(Scene.acquisition_date)\
     .order_by(Scene.acquisition_date.asc())\
     .all()
    
    if not results:
        return []
        
    return [
        {
            "date": r.acquisition_date.strftime("%Y-%m-%d"),
            "vegetation": r.vegetation or 0,
            "sand": r.sand or 0
        }
        for r in results
    ]

@router.get("/shap-values")
def get_shap_values(
    region_id: int = None,
    scene_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if scene_id:
        target_scene = db.query(Scene).filter(Scene.id == scene_id).first()
    elif region_id:
        target_scene = db.query(Scene)\
            .join(ShapValue, Scene.id == ShapValue.scene_id)\
            .filter(Scene.region_id == region_id)\
            .order_by(Scene.acquisition_date.desc())\
            .first()
    else:
        return []
        
    if not target_scene:
        return []
        
    shap_vals = db.query(ShapValue).filter(ShapValue.scene_id == target_scene.id).all()
    
    return [
        { "feature": sv.feature_name, "value": sv.value }
        for sv in shap_vals
    ]

@router.get("/stats")
def get_stats(
    region_id: int = None,
    scene_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    empty_stats = {
        "total_vegetation_area_m2": 0,
        "vegetation_trend_percent": 0.0,
        "avg_confidence": 0.0,
        "confidence_trend_percent": 0.0,
        "active_anomalies": 0,
        "anomalies_trend": 0
    }

    latest_scene = None
    previous_scene = None

    if scene_id:
        latest_scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if latest_scene:
            previous_scene = db.query(Scene)\
                .join(ClassificationResult, Scene.id == ClassificationResult.scene_id)\
                .filter(Scene.region_id == latest_scene.region_id)\
                .filter(Scene.acquisition_date < latest_scene.acquisition_date)\
                .order_by(Scene.acquisition_date.desc())\
                .first()
    elif region_id:
        recent_scenes = db.query(Scene)\
            .join(ClassificationResult, Scene.id == ClassificationResult.scene_id)\
            .filter(Scene.region_id == region_id)\
            .group_by(Scene.id)\
            .order_by(Scene.acquisition_date.desc())\
            .limit(2)\
            .all()
        if recent_scenes:
            latest_scene = recent_scenes[0]
            previous_scene = recent_scenes[1] if len(recent_scenes) > 1 else None

    if not latest_scene:
        return empty_stats
    
    def get_metrics_for_scene(scene_id):
        crs = db.query(ClassificationResult).filter(ClassificationResult.scene_id == scene_id).all()
        veg_cr = next((cr for cr in crs if cr.label == 'vegetation'), None)
        veg_area = veg_cr.area_m2 if veg_cr and veg_cr.area_m2 else 0
        confidences = [cr.confidence for cr in crs if cr.confidence is not None]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        return veg_area, avg_conf

    veg_area, avg_conf = get_metrics_for_scene(latest_scene.id)
    prev_veg_area, prev_avg_conf = get_metrics_for_scene(previous_scene.id) if previous_scene else (veg_area, avg_conf)
    
    # Calculate trends
    veg_trend = ((veg_area - prev_veg_area) / prev_veg_area * 100) if prev_veg_area > 0 else 0
    conf_trend = avg_conf - prev_avg_conf
    
    # Simple anomaly logic: drop in vegetation > 10%
    anomalies = 1 if veg_trend < -10 else 0
    
    return {
       "total_vegetation_area_m2": veg_area,
       "vegetation_trend_percent": round(veg_trend, 1),
       "avg_confidence": round(avg_conf, 1),
       "confidence_trend_percent": round(conf_trend, 1),
       "active_anomalies": anomalies,
       "anomalies_trend": anomalies # simplified
    }
