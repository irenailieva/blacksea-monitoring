from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from sqlalchemy import func, case
from app.models.classification_result import ClassificationResult
from app.models.shap_value import ShapValue
from app.models.scene import Scene

# Инициализираме APIRouter за маршрутите, свързани с анализ на данни.
# Префиксът "/analysis" се добавя към всички пътища тук, а тагът улеснява групирането им в Swagger документацията.
router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/vegetation-trend")
def get_vegetation_trend(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Извлича исторически данни за тренда на вегетацията в даден регион.
    Анализът се базира на класификационните резултати от сателитните снимки (сцени).
    """
    # SQL Заявка:
    # 1. Избираме датата на заснемане (acquisition_date).
    # 2. Сумираме площта (area_m2) само на пикселите, класифицирани като "vegetation".
    # 3. Сумираме площта (area_m2) само на пикселите, класифицирани като "sand".
    # 4. Обединяваме таблицата със сцените и резултатите от класификацията.
    # 5. Филтрираме само сцените, отнасящи се за зададения регион (region_id).
    # 6. Групираме по дата, за да получим агрегираните площи за всеки отделен ден.
    # 7. Подреждаме по дата във възходящ ред (хронологично), за да начертаем графика на тренда.
    results = db.query(
        Scene.acquisition_date,
        func.sum(
            case(
                [(ClassificationResult.label == 'vegetation', ClassificationResult.area_m2)], 
                else_=0
            )
        ).label('vegetation'),
        func.sum(
            case(
                [(ClassificationResult.label == 'sand', ClassificationResult.area_m2)], 
                else_=0
            )
        ).label('sand')
    ).join(ClassificationResult, Scene.id == ClassificationResult.scene_id)\
     .filter(Scene.region_id == region_id)\
     .group_by(Scene.acquisition_date)\
     .order_by(Scene.acquisition_date.asc())\
     .all()
    
    # Ако няма резултати, връщаме празен списък.
    if not results:
        return []
        
    # Преформатираме върнатите данни в списък от речници (JSON обекти),
    # които са удобни за визуализация във frontend-а (напр. с Recharts).
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
    """
    Връща SHAP стойности (SHapley Additive exPlanations) за оценка на важността
    на различните спектрални характеристики (признаци), използвани от модела за класификация.
    Може да се филтрира по конкретна сцена (scene_id) или да се вземе най-скорошната сцена
    за даден регион (region_id).
    """
    
    # 1. Определяне на целевата сцена
    if scene_id:
        # Ако е подадено конкретно ID на сцена, извличаме нея директно
        target_scene = db.query(Scene).filter(Scene.id == scene_id).first()
    elif region_id:
        # Ако е подаден регион, намираме най-новата сцена (order_by desc),
        # за която има генерирани SHAP стойности (постига се чрез join с ShapValue таблицата).
        target_scene = db.query(Scene)\
            .join(ShapValue, Scene.id == ShapValue.scene_id)\
            .filter(Scene.region_id == region_id)\
            .order_by(Scene.acquisition_date.desc())\
            .first()
    else:
        # Ако не е подаден нито scene_id, нито region_id, връщаме празен резултат.
        return []
        
    # Ако целевата сцена не е открита, прекъсваме изпълнението.
    if not target_scene:
        return []
        
    # 2. Извличане на SHAP стойностите за намерената сцена
    shap_vals = db.query(ShapValue).filter(ShapValue.scene_id == target_scene.id).all()
    
    # 3. Трансформиране в лесен за използване формат
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
    """
    Връща обобщени статистически данни за промените и състоянието на екосистемата.
    Включва обща площ на вегетацията, тренд (процентна промяна спрямо предходен период),
    средна увереност (confidence) на ML модела и индикации за аномалии.
    """
    # Шаблон по подразбиране, който ще бъде върнат при липса на данни.
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

    # 1. Идентифициране на текущата (latest) и предходната (previous) сцена за сравнение
    if scene_id:
        # Ако е подадено ID, намираме конкретната сцена
        latest_scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if latest_scene:
            # Търсим най-скорошната сцена преди тази (по дата на заснемане) в същия регион,
            # която има готови класификационни резултати.
            previous_scene = db.query(Scene)\
                .join(ClassificationResult, Scene.id == ClassificationResult.scene_id)\
                .filter(Scene.region_id == latest_scene.region_id)\
                .filter(Scene.acquisition_date < latest_scene.acquisition_date)\
                .order_by(Scene.acquisition_date.desc())\
                .first()
    elif region_id:
        # Ако е подаден регион, взимаме последните две сцени с готови резултати.
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

    # Ако не е намерена дори една сцена, връщаме нулевите статистики
    if not latest_scene:
        return empty_stats
    
    # 2. Помощна функция за извличане на метрики (вегетационна площ и увереност на модела) за дадена сцена
    def get_metrics_for_scene(scene_id):
        # Извличаме всички класификационни резултати за тази сцена
        crs = db.query(ClassificationResult).filter(ClassificationResult.scene_id == scene_id).all()
        # Намираме специфично обекта, класифициран като "vegetation" (вегетация)
        veg_cr = next((cr for cr in crs if cr.label == 'vegetation'), None)
        # Взимаме неговата площ или 0, ако няма такъв запис
        veg_area = veg_cr.area_m2 if veg_cr and veg_cr.area_m2 else 0
        
        # Събираме стойностите за увереност (confidence) и изчисляваме средноаритметично
        confidences = [cr.confidence for cr in crs if cr.confidence is not None]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        
        return veg_area, avg_conf

    # Взимаме метриките за текущата сцена
    veg_area, avg_conf = get_metrics_for_scene(latest_scene.id)
    # Взимаме метриките за предходната сцена (или повтаряме текущите, ако няма предходна, което прави тренда = 0)
    prev_veg_area, prev_avg_conf = get_metrics_for_scene(previous_scene.id) if previous_scene else (veg_area, avg_conf)
    
    # 3. Изчисляване на трендове (процентна разлика)
    # Формула: ((Нова стойност - Стара стойност) / Стара стойност) * 100
    veg_trend = ((veg_area - prev_veg_area) / prev_veg_area * 100) if prev_veg_area > 0 else 0
    conf_trend = avg_conf - prev_avg_conf
    
    # 4. Логика за засичане на аномалии
    # Например: ако вегетацията спадне рязко с над 20%, това е индикатор за проблем
    # (напр. екологична катастрофа или измиране на водорасли)
    anomalies = 1 if veg_trend < -20 else 0
    
    # Връщане на закръглените резултати към frontend-а
    return {
       "total_vegetation_area_m2": veg_area,
       "vegetation_trend_percent": round(veg_trend, 1),
       "avg_confidence": round(avg_conf, 1),
       "confidence_trend_percent": round(conf_trend, 1),
       "active_anomalies": anomalies,
       "anomalies_trend": anomalies # Опростено за нуждите на демото
    }
