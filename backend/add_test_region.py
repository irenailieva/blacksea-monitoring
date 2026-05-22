import sys
import os
from datetime import date, timedelta
from app.core.database import SessionLocal
from app.crud import region, scene, index_value
from app.schemas import RegionCreate, SceneCreate, IndexValueCreate
from app.models.scene import Scene
from app.models.index_type import IndexType
from app.models.classification_result import ClassificationResult
from app.models.shap_value import ShapValue
import random

def add_test_region():
    db = SessionLocal()
    try:
        from sqlalchemy import text
        db.execute(text("ALTER TABLE scenes ADD COLUMN IF NOT EXISTS display_name VARCHAR(100);"))
        db.execute(text("ALTER TABLE classification_results ADD COLUMN IF NOT EXISTS area_m2 FLOAT;"))
        db.commit()
        print("Adding Test Region...")
        
        # 1. Create Region
        coords = [[27.5, 42.5], [28.0, 42.5], [28.0, 43.0], [27.5, 43.0], [27.5, 42.5]]
        geometry = {
            "type": "Polygon",
            "coordinates": [coords]
        }
        
        region_in = RegionCreate(
            name="Burgas Bay (Test)",
            description="Test region for analysis",
            area_km2=500.0,
            geometry=geometry
        )
        try:
            created_region = region.create(db=db, obj_in=region_in)
            region_id = created_region.id
            print(f"Created region ID: {region_id}")
        except Exception as e:
            print("Region already exists, fetching it...")
            db.rollback()
            existing_region = region.get_by_name(db=db, name="Burgas Bay (Test)")
            region_id = existing_region.id
            print(f"Fetched existing region ID: {region_id}")

        # 2. Create Scenes & Classification Results
        print("Creating Scenes and data...")
        today = date.today()
        for i in range(2):
            scene_date = today - timedelta(days=i*30) # One month apart
            scene_id_str = f"S2A_MSIL2A_{scene_date.strftime('%Y%m%d')}_TEST2"
            
            scene_in = SceneCreate(
                scene_id=scene_id_str,
                acquisition_date=scene_date,
                satellite="Sentinel-2",
                cloud_cover=5.0,
                region_id=region_id
            )
            new_scene = scene.create(db=db, obj_in=scene_in)
            
            # Create classification result for vegetation
            veg_area = 15000000.0 if i == 1 else 10000000.0 # Drop from 15m to 10m
            cr_veg = ClassificationResult(
                scene_id=new_scene.id,
                region_id=region_id,
                label='vegetation',
                confidence=85.0 + random.uniform(-5, 5),
                area_m2=veg_area
            )
            db.add(cr_veg)
            
            # Create SHAP values
            shap1 = ShapValue(scene_id=new_scene.id, feature_name="NDWI", value=0.45)
            shap2 = ShapValue(scene_id=new_scene.id, feature_name="Blue_Band", value=0.25)
            shap3 = ShapValue(scene_id=new_scene.id, feature_name="NIR", value=-0.1)
            db.add_all([shap1, shap2, shap3])
            
        db.commit()
        print("Test region and data added successfully!")

    except Exception as e:
        print(f"Failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_region()
