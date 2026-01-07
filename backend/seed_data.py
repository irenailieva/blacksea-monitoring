import os
import json
from datetime import date, timedelta
from app.core.database import SessionLocal
from app.crud import region, scene, index_value
from app.schemas import RegionCreate, SceneCreate, IndexValueCreate
from app.models.scene import Scene

def seed():
    db = SessionLocal()
    try:
        print("Seeding data...")
        
        # 1. Create Region
        existing_region = region.get_multi(db)
        if not existing_region:
            print("Creating Black Sea Region...")
            # Approximate square in Black Sea
            coords = [[29.0, 42.0], [31.0, 42.0], [31.0, 44.0], [29.0, 44.0], [29.0, 42.0]]
            # GeoJSON Polygon
            geometry = {
                "type": "Polygon",
                "coordinates": [coords]
            }
            
            region_in = RegionCreate(
                name="Western Black Sea",
                description="Primary AOI for monitoring",
                area_km2=20000.0,
                geometry=geometry
            )
            created_region = region.create(db=db, obj_in=region_in)
            region_id = created_region.id
        else:
            print("Region already exists.")
            region_id = existing_region[0].id

        # 2. Create Scenes
        print("Creating Scenes...")
        today = date.today()
        created_scenes = []
        for i in range(5):
            scene_date = today - timedelta(days=i*5)
            scene_id_str = f"S2A_MSIL2A_{scene_date.strftime('%Y%m%d')}_T35TQF"
            
            # Check if exists
            existing = db.query(Scene).filter(Scene.scene_id == scene_id_str).first()
            if not existing:
                scene_in = SceneCreate(
                    scene_id=scene_id_str,
                    acquisition_date=scene_date,
                    satellite="Sentinel-2",
                    cloud_cover=5.0 + i,
                    region_id=region_id
                )
                new_scene = scene.create(db=db, obj_in=scene_in)
                created_scenes.append(new_scene)
            else:
                created_scenes.append(existing)

        # 3. Create Index Values (NDVI)
        print("Creating Index Values...")
        # Assume IndexType 1 is NDVI (might need to create if not exists, but usually init migration does it? 
        # checking CRUD for index_type... assuming 'index_types' table empty so let's check or mock ID 1)
        
        # We need an index type first? app/crud/index_type.py...
        # Let's import it
        from app.models.index_type import IndexType
        ndvi_type = db.query(IndexType).filter(IndexType.name == "NDVI").first()
        if not ndvi_type:
            ndvi_type = IndexType(name="NDVI", description="Vegetation Index", formula="(NIR-RED)/(NIR+RED)")
            db.add(ndvi_type)
            db.commit()
            db.refresh(ndvi_type)
            
        ndvi_id = ndvi_type.id
        
        for s in created_scenes:
            # Check if value exists
            existing_val = index_value.get_by_scene(db=db, scene_id=s.id)
            if not existing_val:
                val = 0.4 + (0.1 * (s.id % 3)) # Random ish
                iv_in = IndexValueCreate(
                    scene_id=s.id,
                    index_type_id=ndvi_id,
                    region_id=region_id,
                    mean_value=val,
                    min_value=val - 0.2,
                    max_value=val + 0.2
                )
                index_value.create(db=db, obj_in=iv_in)

        # 4. Create Mock TIF file
        # Ensure directory exists: /app/ml/inference/
        os.makedirs("/app/ml/inference", exist_ok=True)
        for s in created_scenes:
            fname = f"/app/ml/inference/{s.scene_id}_classification.tif"
            if not os.path.exists(fname):
                with open(fname, "w") as f:
                    f.write("Mock TIF Content")
                print(f"Created mock TIF: {fname}")

        print("Seeding completed successfully!")

    except Exception as e:
        print(f"Seeding failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
