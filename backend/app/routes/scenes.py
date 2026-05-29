import shutil
import httpx
import os
from datetime import datetime
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_any_role
from app.models.user import User
from app import schemas
from app.crud import scene as crud_scene
from app.crud import etl_job as crud_etl_job

# Взимаме базовия URL на Machine Learning (ML) услугата от променливите на обкръжението.
# Ако не е зададен, използваме подразбиращия се вътрешен адрес "http://ml:8500".
ML_BASE_URL = os.getenv("ML_BASE_URL", "http://ml:8500")

def to_ml_path(p: str) -> str:
    """
    Превежда пътя от файловата система на бекенд контейнера към съответстващия път в ML контейнера.
    Тъй като двата контейнера може да имат различни точки на монтиране (mount points) на едни и същи 
    docker volumes, тази функция гарантира, че ML услугата ще намери файла.
    """
    abs_p = os.path.abspath(p)
    # Заменя специфичния за бекенда префикс "/app/ml/" с общия за ML услугата "/app/".
    if "/app/ml/" in abs_p:
        return abs_p.replace("/app/ml/", "/app/")
    return p

async def trigger_ml_inference(job_id: int, scene_id_int: int, file_path: str):
    """
    Асинхронна фонова задача, която извиква ML услугата за анализ (inference) на сателитна снимка
    и поддържа статуса на ETL (Extract, Transform, Load) задачата актуален в базата данни.
    """
    # Тъй като се изпълнява във фонов режим (извън обхвата на FastAPI request-а),
    # тук трябва ръчно да създадем и управляваме сесията към базата данни.
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        # Извличаме записа за сцената от базата данни, за да използваме нейния уникален стринг идентификатор.
        # Това помага за консистентно именуване на генерираните файлове.
        from app.crud.scene import scene as crud_scene_local
        db_scene = crud_scene_local.get(db, id=scene_id_int)
        scene_id_str = db_scene.scene_id if db_scene else f"scene_{scene_id_int}"

        # 1. Промяна на статуса на ETL задачата: от "pending" (чакаща) на "processing" (в процес).
        db_job = crud_etl_job.etl_job.get(db, id=job_id)
        if db_job:
            payload_update = dict(db_job.payload or {})
            payload_update["progress"] = 10  # Задаваме начален прогрес от 10%
            crud_etl_job.etl_job.update(
                db, db_obj=db_job,
                obj_in={"status": "processing", "payload": payload_update}
            )

        # 2. Подготовка на пътищата до файловете
        ml_file_path = to_ml_path(file_path)
        output_path = to_ml_path(f"/app/ml/data/inference/{scene_id_str}_classification.tif")

        # 3. Изграждане на JSON заявка за ML модела
        # За ML алгоритъма (напр. Random Forest или XGBoost) е необходимо да подадем пътищата
        # до отделните спектрални канали (B2, B3, B4, B8) и маската за класификация (SCL).
        ml_payload = {
            "b2": ml_file_path,
            "b3": ml_file_path,
            "b4": ml_file_path,
            "b8": ml_file_path,
            "scl": ml_file_path,
            "output_path": output_path
        }

        # 4. Извършване на HTTP POST заявка към вътрешния ML микросървис
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(f"{ML_BASE_URL}/process_scene", json=ml_payload)
            if r.status_code != 200:
                print(f"ML Processing failed for scene {scene_id_str}: {r.status_code} - {r.text}")
            # Извиква изключение, ако отговорът не е HTTP 200 OK
            r.raise_for_status()

        print(f"ML Processing completed successfully for scene {scene_id_str}")
        
        # 5. При успешен отговор актуализираме статуса на задачата на "completed" (завършена).
        db_job = crud_etl_job.etl_job.get(db, id=job_id)
        if db_job:
            payload_done = dict(db_job.payload or {})
            payload_done["progress"] = 100
            crud_etl_job.etl_job.update(
                db, db_obj=db_job,
                obj_in={
                    "status": "completed", 
                    "payload": payload_done,
                    "finished_at": datetime.utcnow()
                }
            )
    except Exception as e:
        # 6. В случай на възникнала грешка в който и да е етап, отбелязваме задачата като "failed"
        print(f"Failed to trigger ML processing: {e}")
        db_job = crud_etl_job.etl_job.get(db, id=job_id)
        if db_job:
            crud_etl_job.etl_job.update(
                db, db_obj=db_job,
                obj_in={"status": "failed", "finished_at": datetime.utcnow()}
            )
    finally:
        # Винаги затваряме сесията към базата данни, за да предотвратим изтичане на ресурси (memory leaks)
        db.close()

# Инициализиране на рутер за маршрути, свързани със "Сцени" (Сателитни снимки)
router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.post("", response_model=schemas.SceneRead, status_code=status.HTTP_201_CREATED)
def create_scene(
    scene_in: schemas.SceneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """
    Създава нов запис за сцена в базата данни.
    Тази функционалност е защитена и изисква роля 'researcher' или 'admin'.
    """
    return crud_scene.create(db=db, obj_in=scene_in)


@router.get("", response_model=List[schemas.SceneRead])
def read_scenes(
    skip: int = 0,
    limit: int = 100,
    region_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Връща списък със сателитни сцени, подредени в обратен хронологичен ред (от най-новите към най-старите).
    Потребителят трябва да е вписан в системата. Поддържа се филтриране по географски регион (region_id).
    """
    from app.models.scene import Scene
    
    print(f"[DEBUG] Fetching scenes for user {current_user.username}, region_id={region_id}")

    # Връщаме всички сцени — не филтрираме по classification_results,
    # защото сцените трябва да се показват в списъка веднага след приключване на ETL,
    # независимо дали ML е генерирал статистика.
    query = db.query(Scene)

    # Ако е предоставен region_id, добавяме допълнителен WHERE филтър.
    if region_id:
        query = query.filter(Scene.region_id == region_id)
        
    # Извличане с отместване (offset) и ограничение (limit) за странициране (pagination).
    res = query.order_by(Scene.acquisition_date.desc(), Scene.id.desc()).offset(skip).limit(limit).all()
    
    print(f"[DEBUG] Returning {len(res)} scenes")
    return res


@router.get("/etl-status", response_model=List[schemas.ETLJobRead])
def get_etl_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Връща статус на последните 10 задачи от ETL конвейера (Pipeline).
    Използва се от frontend-а за визуализация в реално време на прогреса 
    (например progress bar компоненти в потребителския интерфейс).
    """
    return crud_etl_job.etl_job.get_recent_jobs(db, limit=10)

@router.get("/{scene_id}", response_model=schemas.SceneRead)
def read_scene(
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Търси и връща детайлна информация за конкретна сцена въз основа на нейното ID.
    Изисква автентикация.
    """
    db_scene = crud_scene.get(db=db, id=scene_id)
    if not db_scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    return db_scene


@router.put("/{scene_id}", response_model=schemas.SceneRead)
def update_scene(
    scene_id: int,
    scene_in: schemas.SceneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """
    Обновява данните на съществуваща сцена.
    Изисква високи права за достъп (researcher или admin).
    """
    db_scene = crud_scene.get(db=db, id=scene_id)
    if not db_scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    return crud_scene.update(db=db, db_obj=db_scene, obj_in=scene_in)


@router.delete("/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scene(
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("admin"))
):
    """
    Изтрива сателитна сцена от базата данни.
    Това е високорискова операция и е позволена единствено на потребители с роля 'admin'.
    """
    db_scene = crud_scene.get(db=db, id=scene_id)
    if not db_scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    crud_scene.delete(db=db, id=scene_id)
    return None


@router.post("/upload", response_model=schemas.SceneRead)
async def upload_scene_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """
    Маршрут за ръчно качване на GeoTIFF файлове от потребителя.
    Файлът се запазва локално и се нарежда на опашката за ML анализ (Machine Learning).
    Има логика за избягване на дублиране на файлови имена чрез добавяне на времеви маркер (timestamp).
    """
    # 1. Създаване на директория за запазване (ако не съществува)
    upload_dir = Path("/app/ml/data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 2. Генериране на уникално име, базирано на датата и часа по Гринуич (UTC)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    stem = Path(file.filename).stem
    suffix = Path(file.filename).suffix or ".tif"
    unique_filename = f"{stem}_{ts}{suffix}"
    scene_id_str = f"{stem}_{ts}"

    file_path = upload_dir / unique_filename
    
    # 3. Запазване на файла на диска чрез копиране на бинарните данни
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    from app.models.region import Region
    import json
    
    region_id = None
    try:
        import rasterio
        from sqlalchemy import func
        
        # 4. Прочитане на метаданните на качения GeoTIFF чрез rasterio
        with rasterio.open(str(file_path)) as src:
            bounds = src.bounds
            
        # 5. Търсене на географско припокриване (intersection) между снимката и съществуващите региони в базата.
        # Използват се функции на PostGIS (ST_Intersects, ST_MakeEnvelope).
        intersecting = db.query(Region).filter(
            ~Region.name.like("AOI_%"),
            ~Region.name.like("aoi_%"),
            func.ST_Intersects(
                Region.geometry,
                func.ST_MakeEnvelope(bounds.left, bounds.bottom, bounds.right, bounds.top, 4326)
            )
        ).first()
        
        if intersecting:
            # Ако има припокриване, свързваме сцената с открития регион
            region_id = intersecting.id
        else:
            # Ако не е открит регион, автоматично създаваме нов правоъгълен полигон (Area of Interest - AOI)
            aoi_name = f"AOI_{ts}"
            geom = {
                "type": "Polygon",
                "coordinates": [[
                    [bounds.left, bounds.bottom],
                    [bounds.right, bounds.bottom],
                    [bounds.right, bounds.top],
                    [bounds.left, bounds.top],
                    [bounds.left, bounds.bottom]
                ]]
            }
            new_region = Region(
                name=aoi_name,
                description="Автоматично генериран регион (AOI) след ръчно качване",
                area_km2=0.0,
                geometry=func.ST_GeomFromGeoJSON(json.dumps(geom))
            )
            db.add(new_region)
            db.commit()
            db.refresh(new_region)
            region_id = new_region.id
            
    except Exception as e:
        print(f"Geospatial mapping failed: {e}")
        # Запасен вариант (fallback): ако rasterio не е наличен или гръмне, задаваме ID на първия наличен регион
        region = db.query(Region).first()
        region_id = region.id if region else 1

    # 6. Създаване на запис за сцената в базата данни
    scene_in = schemas.SceneCreate(
        scene_id=scene_id_str,
        acquisition_date=datetime.utcnow().date(),
        cloud_cover=None,
        region_id=region_id
    )
    try:
        db_scene = crud_scene.create(db=db, obj_in=scene_in)
    except HTTPException:
        # При конфликт (рядък сценарий), изтриваме вече запазения файл за да не задръстваме сървъра
        file_path.unlink(missing_ok=True)
        raise

    # 7. Генериране на запис за ETL задача с тип "manual_upload"
    job_in = schemas.ETLJobCreate(
        job_type="manual_upload",
        status="pending",
        payload={
            "scene_id": db_scene.id, 
            "scene_id_str": scene_id_str,
            "file_path": str(file_path), 
            "progress": 0
        }
    )
    db_job = crud_etl_job.etl_job.create(db=db, obj_in=job_in.model_dump())

    # 8. Добавяне на фонова задача, която да изпълни тежките ML изчисления без да блокира отговора към потребителя
    background_tasks.add_task(trigger_ml_inference, db_job.id, db_scene.id, str(file_path))

    return db_scene

@router.post("/etl-trigger", response_model=schemas.ETLJobRead)
async def trigger_automated_etl(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """
    Ръчно стартира напълно автоматизиран процес (ETL pipeline) за изтегляне на 
    актуални Sentinel-2 сателитни данни от публичните каталози.
    """
    job_in = schemas.ETLJobCreate(
        job_type="sentinel_auto_pipeline",
        status="pending",
        payload={"progress": 0}
    )
    db_job = crud_etl_job.etl_job.create(db=db, obj_in=job_in.model_dump())
    
    try:
        # Изпращаме HTTP POST към външен микросървис (etl:8001), който отговаря за изтеглянето и обработката.
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("http://etl:8001/trigger", json={"job_id": db_job.id})
            resp.raise_for_status()
    except Exception as e:
        # Ако външната услуга не отговори, маркираме задачата като "failed".
        status_update = schemas.ETLJobUpdate(status="failed")
        db_job = crud_etl_job.etl_job.update(db, db_obj=db_job, obj_in=status_update)
        raise HTTPException(status_code=500, detail=f"Failed to trigger ETL pipeline: {e}")
    
    return db_job


@router.post("/analyze-aoi", response_model=schemas.AoiAnalysisResponse)
async def analyze_aoi(
    request: schemas.AoiAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """
    Потребителски-ориентиран анализ на конкретен правоъгълен полигон (Bounding Box / AOI).
    Потребителят чертае зона на картата, системата пита външни STAC каталози за най-добрата 
    Sentinel-2 сцена над тази територия и задейства ETL+ML конвейера.
    """
    bbox = request.bbox
    
    # Дефинираме уникално име на зоната, базирано на нейните координати.
    # Това предотвратява кеширане и сблъсък с други предварително създадени зони.
    aoi_name = request.aoi_name or f"aoi_{bbox[0]:.3f}_{bbox[1]:.3f}"

    job_in = schemas.ETLJobCreate(
        job_type="aoi_analysis",
        status="pending",
        payload={
            "progress": 0,
            "bbox": bbox,
            "aoi_name": aoi_name,
            "display_name": request.display_name,
            "cloud_max": request.cloud_max,
        }
    )
    db_job = crud_etl_job.etl_job.create(db=db, obj_in=job_in.model_dump())

    try:
        # Уведомяваме специализирания ETL микросървис да започне работа за зададения BBox.
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://etl:8001/trigger",
                json={
                    "job_id": db_job.id,
                    "bbox": bbox,
                    "aoi_name": aoi_name,
                    "display_name": request.display_name,
                    "cloud_max": request.cloud_max,
                }
            )
            resp.raise_for_status()
    except Exception as e:
        crud_etl_job.etl_job.update(db, db_obj=db_job, obj_in={"status": "failed"})
        raise HTTPException(status_code=500, detail=f"Failed to trigger AOI analysis: {e}")

    # Информираме frontend-а, че задачата е стартирана успешно във фонов режим.
    return schemas.AoiAnalysisResponse(
        job_id=db_job.id,
        status="pending",
        message=f"Analysis started for AOI '{aoi_name}'. Poll /scenes/etl-status for progress."
    )


@router.post("/etl-retry/{job_id}", response_model=schemas.ETLJobRead)
async def retry_etl_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """
    Служи за повторен опит (retry) при блокирала или провалена ETL задача.
    Механиката е различна в зависимост от типа на задачата:
    - manual_upload: Изпълнява наново ML модела върху съществуващия локален файл, без да е нужен нов ъплоуд.
    - sentinel_auto_pipeline: Пресъздава изцяло нова заявка към външната ETL услуга.
    """
    from app.models.etl_job import ETLJob as ETLJobModel
    
    # Търсим проблемната задача в базата данни
    original = db.query(ETLJobModel).filter(ETLJobModel.id == job_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="ETL job not found")

    # Позволяваме рестартиране само на провалени или зациклили ("pending") задачи
    if original.status not in ("failed", "pending"):
        raise HTTPException(
            status_code=400,
            detail=f"Only failed or stuck-pending jobs can be retried (current: {original.status})"
        )

    if original.job_type == "manual_upload":
        # За ръчно качени файлове, проверяваме дали оригиналният файл все още е наличен на диска.
        file_path = (original.payload or {}).get("file_path")
        scene_id  = (original.payload or {}).get("scene_id")
        if not file_path or not Path(file_path).exists():
            raise HTTPException(
                status_code=422,
                detail="Original upload file no longer exists — please re-upload the file."
            )
            
        # Нулираме статуса към "pending" и рестартираме фоновата ML задача.
        crud_etl_job.etl_job.update(
            db, db_obj=original,
            obj_in={"status": "pending", "finished_at": None,
                    "payload": {**(original.payload or {}), "progress": 0}}
        )
        background_tasks.add_task(trigger_ml_inference, original.id, scene_id, file_path)
        db.refresh(original)
        return original

    else:
        # За автоматизирани сателитни pipeline-и просто създаваме ново копие на задачата.
        job_in = schemas.ETLJobCreate(
            job_type="sentinel_auto_pipeline",
            status="pending",
            payload={"progress": 0}
        )
        new_job = crud_etl_job.etl_job.create(db=db, obj_in=job_in.model_dump())
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post("http://etl:8001/trigger", json={"job_id": new_job.id})
                resp.raise_for_status()
        except Exception as e:
            crud_etl_job.etl_job.update(db, db_obj=new_job, obj_in={"status": "failed"})
            raise HTTPException(status_code=500, detail=f"ETL service unreachable: {e}")
        return new_job
