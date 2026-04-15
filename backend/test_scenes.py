from app.core.database import SessionLocal
from app.crud.scene import scene

db = SessionLocal()
res = scene.get_multi(db=db, limit=100)
for r in res:
    print(f"id={r.id} scene_id={r.scene_id} cloud={r.cloud_cover} date={r.acquisition_date}")
