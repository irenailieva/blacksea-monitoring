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
# We don't need to redefine Base since we are using the models directly

def upload_to_db(file_path: str, db_url: str, aoi_config: dict, scene_id: str = None, acquisition_date: date = None):
    """
    Uploads metadata of the processed file to PostGIS using the backend schema.
    
    Args:
        file_path (str): Path to the file to upload.
        db_url (str): Database connection URL.
        aoi_config (dict): AOI configuration including name and bbox.
        scene_id (str): Optional Scene ID override.
    """
    logger.info(f"Uploading metadata for {file_path} to DB...")
    
    # Create the database engine which manages the connection pool
    engine = create_engine(db_url)
    
    # Create a configured "Session" class
    Session = sessionmaker(bind=engine)
    # Create a Session instance to interact with the database
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
                # Compute approximate area in km² from bounding box
                import math
                lat_mid = (miny + maxy) / 2.0
                width_km = abs(maxx - minx) * 111.32 * math.cos(math.radians(lat_mid))
                height_km = abs(maxy - miny) * 110.57
                computed_area_km2 = max(round(width_km * height_km, 4), 0.0001)
                # Use WKTElement for PostGIS geometry
                geometry_element = WKTElement(wkt_geom, srid=4326)
                region = Region(
                    name=region_name,
                    geometry=geometry_element,
                    area_km2=computed_area_km2
                )
                session.add(region)
                session.commit()
                session.refresh(region)
            
            # 2. Get or Create Scene
            filename = os.path.basename(file_path)
            
            # Use provided scene_id or extract from filename
            scene_identifier = scene_id
            if not scene_identifier:
                if filename.startswith("sentinel2_"):
                    # Strip '.tif' and suffixes like '_classification', '_processed', etc.
                    scene_identifier = filename.split(".tif")[0]
                    # Further strip common suffixes to get the base scene ID
                    for suffix in ["_processed", "_classification", "_NDVI"]:
                        if suffix in scene_identifier:
                            scene_identifier = scene_identifier.split(suffix)[0]
                else:
                    # Fallback for manual uploads or other formats
                    scene_identifier = filename.split(".")[0]
            
            scene = session.query(Scene).filter_by(scene_id=scene_identifier).first()
            if not scene:
                logger.info(f"Creating new scene: {scene_identifier}")
                scene = Scene(
                    scene_id=scene_identifier,
                    acquisition_date=acquisition_date or datetime.utcnow().date(),
                    satellite="Sentinel-2",
                    region_id=region.id,
                    cloud_cover=0.0
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
            if "classification" in filename:
                file_type = "CLASSIFICATION"
            
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
