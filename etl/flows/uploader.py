import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
import rasterio
from shapely.geometry import box

# Import models from the backend
# Ensure 'backend' is in PYTHONPATH or mounted at /app/backend
from backend.app.models.region import Region
from backend.app.models.scene import Scene
from backend.app.models.scene_file import SceneFile
# We don't need to redefine Base since we are using the models directly

def upload_to_db(file_path: str, db_url: str, aoi_config: dict):
    """
    Uploads metadata of the processed file to PostGIS using the backend schema.
    
    Args:
        file_path (str): Path to the file to upload.
        db_url (str): Database connection URL.
        aoi_config (dict): AOI configuration including name and bbox.
    """
    logger.info(f"Uploading metadata for {file_path} to DB...")
    
    engine = create_engine(db_url)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        with rasterio.open(file_path) as src:
            bounds = src.bounds
            # Create WKT geometry from bounds
            minx, miny, maxx, maxy = bounds.left, bounds.bottom, bounds.right, bounds.top
            wkt_geom = f"POLYGON(({minx} {miny}, {minx} {maxy}, {maxx} {maxy}, {maxx} {miny}, {minx} {miny}))"
            
            # 1. Get or Create Region
            region_name = aoi_config.get("name", "unknown_region")
            region = session.query(Region).filter_by(name=region_name).first()
            if not region:
                logger.info(f"Creating new region: {region_name}")
                region = Region(
                    name=region_name,
                    geometry=wkt_geom, # Using the first file's bounds as region geom for now
                    area_km2=0.0 # Placeholder
                )
                session.add(region)
                session.commit()
                session.refresh(region)
            
            # 2. Get or Create Scene
            filename = os.path.basename(file_path)
            acquisition_date = datetime.utcnow().date() # Should extract from metadata
            
            scene_identifier = f"S2_MOCK_{acquisition_date.strftime('%Y%m%d')}_{region_name}"
            
            scene = session.query(Scene).filter_by(scene_id=scene_identifier).first()
            if not scene:
                logger.info(f"Creating new scene: {scene_identifier}")
                scene = Scene(
                    scene_id=scene_identifier,
                    acquisition_date=acquisition_date,
                    satellite="Sentinel-2",
                    region_id=region.id,
                    cloud_cover=0.0 # Placeholder
                )
                session.add(scene)
                session.commit()
                session.refresh(scene)
            
            # 3. Create SceneFile
            file_type = "RAW"
            if "processed" in filename:
                file_type = "L2A"
            if "NDVI" in filename:
                file_type = "NDVI"
            
            existing_file = session.query(SceneFile).filter_by(scene_id=scene.id, file_type=file_type).first()
            if existing_file:
                logger.info(f"File {file_type} for scene {scene_identifier} already exists. Updating path.")
                existing_file.path = file_path
                existing_file.size_bytes = os.path.getsize(file_path)
            else:
                new_file = SceneFile(
                    scene_id=scene.id,
                    file_type=file_type,
                    path=file_path,
                    size_bytes=os.path.getsize(file_path)
                )
                session.add(new_file)
            
            session.commit()
            logger.success(f"Metadata uploaded for {filename} (Type: {file_type})")
            
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to upload to DB: {e}")
        raise
    finally:
        session.close()
