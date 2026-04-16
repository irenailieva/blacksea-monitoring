import os
import sys
import json
import yaml
import datetime
import requests
from dotenv import load_dotenv
from loguru import logger
from flows.downloader import download_data
from flows.index_generator import generate_index
from flows.preprocessor import preprocess_raster
from flows.uploader import upload_to_db

# Load env vars
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

# Add project root to sys.path to allow importing backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from sqlalchemy import create_engine, text
from backend.app.models import Base

def update_job_status(engine, job_id, status, progress=None):
    if not job_id:
        return
    try:
        with engine.begin() as conn:
            if progress is not None:
                # jsonb_set requires a valid JSONB literal — json.dumps() gives us '5' not "'5'"
                progress_json = json.dumps(progress)
                prog_str = (
                    f", payload = jsonb_set(COALESCE(payload::jsonb, '{{}}'::jsonb), "
                    f"'{{progress}}', '{progress_json}'::jsonb)::json "
                )
            else:
                prog_str = ""
            finish_str = ", finished_at = NOW() " if status in ('completed', 'failed') else ""
            stmt = (
                f"UPDATE etl_jobs SET status = :status, updated_at = NOW() "
                f"{prog_str}{finish_str}WHERE id = :job_id"
            )
            conn.execute(text(stmt), {"status": status, "job_id": job_id})
            logger.info(f"Job {job_id} → {status}" + (f" ({progress}%)" if progress is not None else ""))
    except Exception as e:
        logger.error(f"Failed to update job status for job {job_id}: {e}")



def load_config():
    # Force absolute path resolution to avoid CWD issues
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config.yml")
    
    if not os.path.exists(config_path):
        logger.warning(f"Config not found at {config_path}, trying fallback...")
        config_path = "config.yml"
        
    logger.info(f"Loading config from: {os.path.abspath(config_path)}")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        if not config:
            raise ValueError(f"Config file at {config_path} is empty or malformed.")
        return config

def run_pipeline(job_id=None, bbox=None, aoi_name=None, cloud_max=None):
    logger.info(f"Starting ETL pipeline (Job ID: {job_id})")
    
    config = load_config()
    
    # Get settings from env or config
    mode = os.getenv("ETL_MODE", "real")
    output_dir = os.getenv("ETL_OUT_DIR", config['output']['dir'])
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        logger.error("DATABASE_URL is not set!")
        return
        
    # Override output dir to shared ml volume for integration
    # ETL mounts ./ml to /app/ml
    # ML mounts ./ml to /app
    output_dir = "ml/data/inference"

    # Ensure tables exist
    logger.info("Ensuring database tables exist...")
    engine = create_engine(db_url)
    
    # Create ENUM types first
    from backend.app.models.user import user_role
    from backend.app.models.team import team_role
    user_role.create(bind=engine, checkfirst=True)
    team_role.create(bind=engine, checkfirst=True)
    
    Base.metadata.create_all(engine)
    
    update_job_status(engine, job_id, 'processing', 5)

    try:
        # Rolling 90-day window ending today
        import datetime as dt_module
        today = dt_module.date.today()
        since_default = (today - dt_module.timedelta(days=90)).isoformat()
        to_default = today.isoformat()

        time_range = {
            "start_date": config['time'].get('since') or since_default,
            "end_date": config['time'].get('to') or to_default,
        }

        # Use caller-supplied AOI when present, otherwise fall back to config
        effective_aoi = dict(config['aoi'])
        if bbox and len(bbox) == 4:
            effective_aoi['bbox'] = bbox
        if aoi_name:
            effective_aoi['name'] = aoi_name
        effective_cloud_max = cloud_max if cloud_max is not None else config['filters'].get('cloud_max', 20)

        logger.info(f"AOI: {effective_aoi['name']}  bbox={effective_aoi['bbox']}  cloud_max={effective_cloud_max}%")

        download_result = download_data(
            aoi=effective_aoi,
            time_range=time_range,
            output_dir=output_dir,
            mode=mode,
            cloud_max=effective_cloud_max,
        )

        # Pre-flight: check if the downloaded scene already exists in DB
        stac_item_id = download_result.get("stac_item_id", "")
        all_stac_ids = download_result.get("all_stac_ids", [stac_item_id])
        expected_scene_id = f"sentinel2_{stac_item_id}" if stac_item_id else None

        if expected_scene_id:
            from sqlalchemy import text as sql_text
            with engine.connect() as conn:
                rows = conn.execute(
                    sql_text("SELECT scene_id FROM scenes WHERE scene_id = :sid"),
                    {"sid": expected_scene_id}
                ).fetchall()
            if rows:
                logger.info(
                    f"Scene '{expected_scene_id}' already in DB — "
                    f"no new data available from STAC. Marking job as up-to-date."
                )
                update_job_status(engine, job_id, 'completed', 100)
                return

        raw_file = download_result["composite"]
        ml_bands = download_result["ml_bands"]

        
        update_job_status(engine, job_id, 'processing', 30)
        
        # 2. Preprocess
        processed_file = preprocess_raster(raw_file)
        
        update_job_status(engine, job_id, 'processing', 50)
        
        # 3. Generate Index (NDVI)
        ndvi_file = generate_index(processed_file, index_name='NDVI')
        
        update_job_status(engine, job_id, 'processing', 70)
        
        # 4. Upload Metadata
        # Extract Scene ID and Date once from the composite filename
        def get_scene_metadata(f):
            fname = os.path.basename(f)
            sid = ""
            dt = datetime.datetime.utcnow().date()
            
            if fname.startswith("sentinel2_"):
                sid = fname.split(".tif")[0]
                # sentinel2_S2B_35TNH_20240122_0_L2A
                parts = sid.split("_")
                if len(parts) >= 4:
                    date_str = parts[3] # 20240122
                    try:
                        from datetime import datetime as dt_obj
                        dt = dt_obj.strptime(date_str, "%Y%m%d").date()
                    except:
                        pass
            else:
                sid = fname.split(".")[0].replace("_processed", "").replace("_NDVI", "").replace("_classification", "")
            
            return sid, dt

        scene_id_override, real_acquisition_date = get_scene_metadata(raw_file)

        upload_to_db(raw_file, db_url, config['aoi'], scene_id=scene_id_override, acquisition_date=real_acquisition_date)
        upload_to_db(processed_file, db_url, config['aoi'], scene_id=scene_id_override, acquisition_date=real_acquisition_date)
        upload_to_db(ndvi_file, db_url, config['aoi'], scene_id=scene_id_override, acquisition_date=real_acquisition_date)
        
        update_job_status(engine, job_id, 'processing', 90)
        
        # 5. ML Inference
        logger.info("Triggering ML Inference...")
        # Use ML_BASE_URL if set (docker-compose sets ML_BASE_URL for backend, check if set for ETL)
        # Default to http://ml:8500 as per docker-compose service name
        ml_url = os.getenv("ML_BASE_URL", "http://ml:8500")
        
        # Define output path for classification map
        # Output should be in the same volume/dir
        output_filename = os.path.basename(raw_file).replace(".tif", "_classification.tif")
        output_path = os.path.join(output_dir, output_filename)
        
        # Helper to translate ETL path (/app/ml/...) to ML container path (/app/...)
        def to_ml_path(p):
            abs_p = os.path.abspath(p)
            # /app/ml/data/inference/... -> /app/data/inference/...
            if "/app/ml/" in abs_p:
                return abs_p.replace("/app/ml/", "/app/")
            # Fallback if using relative paths or different mount
            if p.startswith("ml/"):
                return p.replace("ml/", "", 1)
            return p
        
        payload = {
            "b2": to_ml_path(ml_bands["b2"]),
            "b3": to_ml_path(ml_bands["b3"]),
            "b4": to_ml_path(ml_bands["b4"]),
            "b8": to_ml_path(ml_bands["b8"],),
            "scl": to_ml_path(ml_bands["scl"]),
            "output_path": to_ml_path(output_path)
        }
        
        try:
            resp = requests.post(f"{ml_url}/process_scene", json=payload)
            if resp.status_code == 200:
                logger.success(f"ML Inference completed. Output: {output_path}")
                # Upload ML output metadata
                upload_to_db(output_path, db_url, config['aoi'], scene_id=scene_id_override, acquisition_date=real_acquisition_date)
            else:
                logger.error(f"ML Inference failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"Failed to contact ML service: {e}")
        
        logger.success("ETL Pipeline completed successfully!")
        update_job_status(engine, job_id, 'completed', 100)
        
    except Exception as e:
        logger.exception(f"ETL Pipeline failed: {e}")
        update_job_status(engine, job_id, 'failed')
        raise

if __name__ == "__main__":
    run_pipeline()
