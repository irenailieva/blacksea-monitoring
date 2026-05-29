import os
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
import rasterio
from shapely.geometry import box
from geoalchemy2 import WKTElement

# Import models from the backend
# Ensure 'backend' is in PYTHONPATH or mounted at /app/backend
from backend.app.models.region import Region
from backend.app.models.scene import Scene
from backend.app.models.scene_file import SceneFile
from backend.app.models.classification_result import ClassificationResult
from backend.app.models.shap_value import ShapValue
from backend.app.models.model_run import ModelRun
from backend.app.models.index_type import IndexType

# Функция за качване на метаданните и резултатите от обработените файлове в PostGIS базата данни
def upload_to_db(file_path: str, db_url: str, aoi_config: dict, scene_id: str = None, acquisition_date: date = None, cloud_cover: float = 0.0, stats: dict = None, shap_data: list = None, display_name: str = None):
    """
    Uploads metadata of the processed file to PostGIS using the backend schema.
    
    Args:
        file_path (str): Path to the file to upload.
        db_url (str): Database connection URL.
        aoi_config (dict): AOI configuration including name and bbox.
        scene_id (str): Optional Scene ID override.
        acquisition_date (date): Date of scene.
        cloud_cover (float): Cloud cover percentage.
    """
    logger.info(f"Uploading metadata for {file_path} to DB...")
    
    # Създаване на SQLAlchemy engine, който управлява пула (pool) от връзки към базата данни
    engine = create_engine(db_url)
    
    # Дефиниране на клас Session, свързан със създадения engine
    Session = sessionmaker(bind=engine)
    # Инстанциране на сесия за извършване на транзакции към базата данни
    session = Session()
    
    try:
        # Отваряне на растерния файл за извличане на географските му граници
        with rasterio.open(file_path) as src:
            bounds = src.bounds
            # Създаване на WKT (Well-Known Text) репрезентация на полигона, обхващащ границите на изображението
            minx, miny, maxx, maxy = bounds.left, bounds.bottom, bounds.right, bounds.top
            wkt_geom = f"POLYGON(({minx} {miny}, {minx} {maxy}, {maxx} {maxy}, {maxx} {miny}, {minx} {miny}))"
            
            # 1. Намиране на регион (Region) — винаги избираме най-близкия предефиниран
            #    (именуван) регион по географски принцип, вместо да създаваме нови AOI_* редове.
            #    Така сцените се агрегират коректно под Varna Bay, Burgas Bay и т.н.
            from sqlalchemy import text as sa_text
            centroid_lon = (minx + maxx) / 2.0
            centroid_lat = (miny + maxy) / 2.0

            nearest_row = session.execute(
                sa_text("""
                    SELECT id, name
                    FROM regions
                    WHERE name NOT LIKE 'AOI\_%' ESCAPE '\\'
                    ORDER BY ST_Distance(
                        ST_Centroid(geometry),
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
                    )
                    LIMIT 1
                """),
                {"lon": centroid_lon, "lat": centroid_lat}
            ).fetchone()

            if nearest_row:
                region = session.query(Region).filter_by(id=nearest_row.id).first()
                logger.info(f"Matched AOI to nearest named region: '{region.name}' (id={region.id})")
            else:
                # Fallback: no named regions exist yet — create one with the AOI name
                region_name = aoi_config.get("name", "unknown_region")
                region = session.query(Region).filter_by(name=region_name).first()
                if not region:
                    logger.warning(f"No named regions found. Creating fallback: {region_name}")
                    import math
                    lat_mid = (miny + maxy) / 2.0
                    width_km = abs(maxx - minx) * 111.32 * math.cos(math.radians(lat_mid))
                    height_km = abs(maxy - miny) * 110.57
                    computed_area_km2 = max(round(width_km * height_km, 4), 0.0001)
                    geometry_element = WKTElement(wkt_geom, srid=4326)
                    region = Region(
                        name=region_name,
                        geometry=geometry_element,
                        area_km2=computed_area_km2
                    )
                    session.add(region)
                    session.commit()
                    session.refresh(region)

            
            # 2. Търсене или създаване на сцена (Scene)
            filename = os.path.basename(file_path)
            
            # Използване на подадения scene_id или извличането му от името на файла
            scene_identifier = scene_id
            if not scene_identifier:
                if filename.startswith("sentinel2_"):
                    # Премахване на '.tif' и суфикси като '_classification', '_processed' и др.
                    scene_identifier = filename.split(".tif")[0]
                    # Допълнително премахване на общи суфикси, за да се получи базовият идентификатор на сцената
                    for suffix in ["_processed", "_classification", "_NDVI"]:
                        if suffix in scene_identifier:
                            scene_identifier = scene_identifier.split(suffix)[0]
                else:
                    # Резервен вариант (fallback) за ръчно качени файлове или различни формати
                    scene_identifier = filename.split(".")[0]
            
            # Търсене на сцената в базата
            scene = session.query(Scene).filter_by(scene_id=scene_identifier).first()
            if not scene:
                logger.info(f"Creating new scene: {scene_identifier}")
                scene = Scene(
                    scene_id=scene_identifier,
                    acquisition_date=acquisition_date or datetime.utcnow().date(),
                    satellite="Sentinel-2",
                    region_id=region.id,
                    cloud_cover=cloud_cover,
                    display_name=display_name
                )
                session.add(scene)
                session.commit()
                session.refresh(scene)
            elif scene.region_id != region.id:
                # Обновяване на съществуваща сцена, ако принадлежи към различен регион
                logger.info(f"Updating existing scene {scene_identifier} to new region: {region_name}")
                scene.region_id = region.id
                session.commit()
                session.refresh(scene)
            
            # 3. Създаване на запис за файла (SceneFile)
            # Определяне на типа на файла на базата на името му
            file_type = "RAW"
            if "processed" in filename:
                file_type = "L2A"
            if "NDVI" in filename:
                file_type = "NDVI"
            if "classification" in filename:
                file_type = "CLASSIFICATION"
            
            # Проверка дали вече съществува запис за този тип файл към тази сцена
            existing_file = session.query(SceneFile).filter_by(scene_id=scene.id, file_type=file_type).first()
            if existing_file:
                logger.info(f"File {file_type} for scene {scene_identifier} already exists. Updating path.")
                # Обновяване на пътя и размера
                existing_file.path = file_path
                existing_file.size_bytes = os.path.getsize(file_path)
            else:
                # Създаване на нов запис за файла
                new_file = SceneFile(
                    scene_id=scene.id,
                    file_type=file_type,
                    path=file_path,
                    size_bytes=os.path.getsize(file_path)
                )
                session.add(new_file)
            
            # Запазване на промените
            session.commit()
            logger.success(f"Metadata uploaded for {filename} (Type: {file_type})")
            
            # 4. Вмъкване на статистически данни и SHAP стойности, ако това е резултат от класификация
            if file_type == "CLASSIFICATION" and stats:
                logger.info("Inserting classification stats and SHAP values...")
                
                # Търсене или създаване на ModelRun (запис за изпълнението на ML модела)
                model_run = session.query(ModelRun).first()
                if not model_run:
                    model_run = ModelRun(model_name="Ensemble_v1", status="completed")
                    session.add(model_run)
                    session.commit()
                    session.refresh(model_run)
                
                # Подготовка на списък с площите (в кв.м.) за всеки класифициран обект
                areas = [
                    ("vegetation", stats.get("vegetation_area_m2")),
                    ("sand", stats.get("sand_area_m2")),
                    ("water", stats.get("water_area_m2"))
                ]
                
                # Изтриване на стари резултати за същата сцена, за да се избегне дублиране
                session.query(ClassificationResult).filter_by(scene_id=scene.id).delete()
                
                # Добавяне на новите резултати
                for label, area in areas:
                    if area is not None:
                        cr = ClassificationResult(
                            model_run_id=model_run.id,
                            scene_id=scene.id,
                            region_id=region.id,
                            label=label,
                            confidence=stats.get("avg_confidence"),
                            area_m2=area
                        )
                        session.add(cr)
                
                # Вмъкване на SHAP стойности (анализ на значимостта на характеристиките)
                if shap_data:
                    # Имената на характеристиките съответстват по ред на спектралните канали и индекси
                    feature_names = ["Blue (B2)", "Green (B3)", "Red (B4)", "NIR (B8)", "NDVI", "NDWI"]
                    
                    # Изтриване на стари SHAP стойности за тази сцена
                    session.query(ShapValue).filter_by(scene_id=scene.id).delete()
                    
                    # Итерация през получените SHAP стойности
                    for idx, val in enumerate(shap_data):
                        fname = feature_names[idx] if idx < len(feature_names) else f"Feature_{idx}"
                        
                        # Търсене или създаване на IndexType (речник за типове индекси)
                        itype = session.query(IndexType).filter_by(name=fname).first()
                        if not itype:
                            itype = IndexType(name=fname, formula="N/A", description="SHAP feature")
                            session.add(itype)
                            session.commit()
                            session.refresh(itype)
                            
                        # Създаване на нов запис за SHAP стойността
                        sv = ShapValue(
                            model_run_id=model_run.id,
                            scene_id=scene.id,
                            index_type_id=itype.id,
                            feature_name=fname,
                            value=val
                        )
                        session.add(sv)
                
                session.commit()
                logger.success("Stats and SHAP values inserted.")
            
    except Exception as e:
        # В случай на грешка, отмяна (rollback) на всички незавършени транзакции
        session.rollback()
        logger.error(f"Failed to upload to DB: {e}")
        raise
    finally:
        # Гарантирано затваряне на сесията, за да се освободят ресурсите към базата данни
        session.close()
