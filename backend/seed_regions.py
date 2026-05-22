import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, text
from app.core.database import SessionLocal, engine
from app.models.region import Region
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Predefined regions along the Bulgarian Coastline
COASTAL_REGIONS = [
    {
        "name": "Varna Bay",
        "description": "Varna Bay and surrounding coastal waters.",
        "area_km2": 45.2,
        "bbox": [27.88, 43.15, 28.05, 43.23] # [minLon, minLat, maxLon, maxLat]
    },
    {
        "name": "Burgas Bay",
        "description": "The largest bay of the Bulgarian Black Sea Coast.",
        "area_km2": 150.0,
        "bbox": [27.45, 42.40, 27.70, 42.60]
    },
    {
        "name": "Cape Kaliakra",
        "description": "Nature and archaeological reserve coastline.",
        "area_km2": 25.5,
        "bbox": [28.40, 43.35, 28.52, 43.42]
    },
    {
        "name": "Nesebar Bay (Sunny Beach)",
        "description": "Coastal waters along Sunny Beach and Nesebar peninsula.",
        "area_km2": 35.8,
        "bbox": [27.70, 42.65, 27.80, 42.73]
    },
    {
        "name": "Sozopol Bay",
        "description": "Historic Sozopol coastal area.",
        "area_km2": 18.4,
        "bbox": [27.65, 42.40, 27.72, 42.45]
    }
]

def bbox_to_geojson_polygon(bbox):
    min_lon, min_lat, max_lon, max_lat = bbox
    return {
        "type": "Polygon",
        "coordinates": [[
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat]
        ]]
    }

def seed_regions():
    db: Session = SessionLocal()
    from sqlalchemy import func
    
    try:
        added = 0
        for reg_data in COASTAL_REGIONS:
            # Check if region already exists
            existing = db.query(Region).filter(Region.name == reg_data["name"]).first()
            if existing:
                logger.info(f"Region '{reg_data['name']}' already exists. Skipping.")
                continue
                
            geom_json = bbox_to_geojson_polygon(reg_data["bbox"])
            
            new_region = Region(
                name=reg_data["name"],
                description=reg_data["description"],
                area_km2=reg_data["area_km2"],
                geometry=func.ST_GeomFromGeoJSON(json.dumps(geom_json))
            )
            db.add(new_region)
            added += 1
            
        if added > 0:
            db.commit()
            logger.info(f"Successfully seeded {added} new regions!")
        else:
            logger.info("No new regions were added. Database is already seeded.")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed regions: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting database region seeding...")
    seed_regions()
    logger.info("Done.")
