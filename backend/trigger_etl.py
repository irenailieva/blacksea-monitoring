from app.core.database import SessionLocal
import httpx
from app.models.etl_job import ETLJob
import asyncio
from datetime import datetime

async def run():
    db = SessionLocal()
    j = ETLJob(job_type="sentinel_auto_pipeline", status="pending")
    db.add(j)
    db.commit()
    db.refresh(j)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post("http://etl:8001/trigger", json={"job_id": j.id})
        print(f"Triggered job {j.id}: {r.status_code}")

asyncio.run(run())
