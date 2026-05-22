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

def run_pipeline(job_id=None, bbox=None, aoi_name=None, cloud_max=None, display_name=None):
    logger.info(f"Starting ETL pipeline (Job ID: {job_id})")
    
    config = load_config()
    
    mode = os.getenv("ETL_MODE", "real")
    output_dir = os.getenv("ETL_OUT_DIR", config['output']['dir'])
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        logger.error("DATABASE_URL is not set!")
        return
        
    output_dir = "ml/data/inference"

    logger.info("Ensuring database tables exist...")
    engine = create_engine(db_url)
    
    from backend.app.models.user import user_role
    from backend.app.models.team import team_role
    user_role.create(bind=engine, checkfirst=True)
    team_role.create(bind=engine, checkfirst=True)
    
    Base.metadata.create_all(engine)
    
    update_job_status(engine, job_id, 'processing', 5)

    try:
        import datetime as dt_module
        today = dt_module.date.today()
        since_default = (today - dt_module.timedelta(days=90)).isoformat()
        to_default = today.isoformat()

        time_range = {
            "start_date": config['time'].get('since') or since_default,
            "end_date": config['time'].get('to') or to_default,
        }

        aoi_list = []
        if bbox and len(bbox) == 4 and aoi_name:
            aoi_list.append({
                "name": aoi_name,
                "bbox": bbox
            })
        else:
            logger.info("Fetching all active regions from database for ETL processing...")
            with engine.connect() as conn:
                rows = conn.execute(text("""
                    SELECT name, 
                           ST_XMin(geometry::geometry) as minx, 
                           ST_YMin(geometry::geometry) as miny, 
                           ST_XMax(geometry::geometry) as maxx, 
                           ST_YMax(geometry::geometry) as maxy 
                    FROM regions 
                    WHERE name NOT LIKE 'AOI_%' AND name NOT LIKE 'aoi_%'
                """)).fetchall()
                for row in rows:
                    if row[1] is not None and row[2] is not None and row[3] is not None and row[4] is not None:
                        aoi_list.append({
                            "name": row[0],
                            "bbox": [row[1], row[2], row[3], row[4]]
                        })
            
            if not aoi_list:
                logger.warning("No active regions found in database. Falling back to config.yml.")
                aoi_list.append(dict(config['aoi']))

        effective_cloud_max = cloud_max if cloud_max is not None else config['filters'].get('cloud_max', 20)

        total_aois = len(aoi_list)
        logger.info(f"Pipeline will process {total_aois} region(s).")

        for idx, effective_aoi in enumerate(aoi_list):
            logger.info(f"Processing AOI {idx+1}/{total_aois}: {effective_aoi['name']}  bbox={effective_aoi['bbox']}  cloud_max={effective_cloud_max}%")
            
            base_progress = 5 + (idx / total_aois) * 90
            region_progress_step = 90 / total_aois

            download_result = download_data(
                aoi=effective_aoi,
                time_range=time_range,
                output_dir=output_dir,
                mode=mode,
                cloud_max=effective_cloud_max,
                progress_callback=lambda p: update_job_status(engine, job_id, 'processing', base_progress + (p / 100) * region_progress_step * 0.2)
            )

            stac_item_id = download_result.get("stac_item_id", "")
            all_stac_ids = download_result.get("all_stac_ids", [stac_item_id])
            expected_scene_id = f"sentinel2_{stac_item_id}" if stac_item_id else None

            if expected_scene_id:
                with engine.connect() as conn:
                    rows = conn.execute(
                        text("""
                            SELECT s.scene_id 
                            FROM scenes s 
                            JOIN scene_files f ON s.id = f.scene_id 
                            JOIN regions r ON s.region_id = r.id
                            WHERE s.scene_id = :sid 
                              AND f.file_type = 'CLASSIFICATION'
                              AND r.name = :rname
                        """),
                        {"sid": expected_scene_id, "rname": effective_aoi['name']}
                    ).fetchall()
                if rows:
                    logger.info(f"Scene '{expected_scene_id}' already in DB for region '{effective_aoi['name']}' — skipping.")
                    continue

            raw_file = download_result.get("composite")
            ml_bands = download_result.get("ml_bands")
            
            if not raw_file or not ml_bands:
                logger.warning(f"No valid data returned for {effective_aoi['name']}, skipping.")
                continue

            update_job_status(engine, job_id, 'processing', base_progress + region_progress_step * 0.3)
            
            processed_file = preprocess_raster(raw_file)
            update_job_status(engine, job_id, 'processing', base_progress + region_progress_step * 0.5)
            
            ndvi_file = generate_index(processed_file, index_name='NDVI')
            update_job_status(engine, job_id, 'processing', base_progress + region_progress_step * 0.7)
            
            def get_scene_metadata(f):
                fname = os.path.basename(f)
                sid = ""
                dt = datetime.datetime.utcnow().date()
                if fname.startswith("sentinel2_"):
                    sid = fname.split(".tif")[0]
                    parts = sid.split("_")
                    if len(parts) >= 4:
                        date_str = parts[3]
                        try:
                            from datetime import datetime as dt_obj
                            dt = dt_obj.strptime(date_str, "%Y%m%d").date()
                        except:
                            pass
                else:
                    sid = fname.split(".")[0].replace("_processed", "").replace("_NDVI", "").replace("_classification", "")
                return sid, dt

            scene_id_override, real_acquisition_date = get_scene_metadata(raw_file)
            scene_id_override = f"{scene_id_override}_job{job_id}_{idx}"
            real_cloud_cover = download_result.get("cloud_cover", 0.0)

            upload_to_db(raw_file, db_url, effective_aoi, scene_id=scene_id_override, acquisition_date=real_acquisition_date, cloud_cover=real_cloud_cover, display_name=display_name)
            upload_to_db(processed_file, db_url, effective_aoi, scene_id=scene_id_override, acquisition_date=real_acquisition_date, cloud_cover=real_cloud_cover, display_name=display_name)
            upload_to_db(ndvi_file, db_url, effective_aoi, scene_id=scene_id_override, acquisition_date=real_acquisition_date, cloud_cover=real_cloud_cover, display_name=display_name)
            
            update_job_status(engine, job_id, 'processing', base_progress + region_progress_step * 0.9)
            
            logger.info(f"Triggering ML Inference for {effective_aoi['name']}...")
            ml_url = os.getenv("ML_BASE_URL", "http://ml:8500")
            
            output_filename = os.path.basename(raw_file).replace(".tif", f"_job{job_id}_{idx}_classification.tif")
            output_path = os.path.join(output_dir, output_filename)
            
            def to_ml_path(p):
                abs_p = os.path.abspath(p)
                if "/app/ml/" in abs_p:
                    return abs_p.replace("/app/ml/", "/app/")
                if p.startswith("ml/"):
                    return p.replace("ml/", "", 1)
                return p
            
            payload = {
                "b2": to_ml_path(ml_bands["b2"]),
                "b3": to_ml_path(ml_bands["b3"]),
                "b4": to_ml_path(ml_bands["b4"]),
                "b8": to_ml_path(ml_bands["b8"]),
                "scl": to_ml_path(ml_bands["scl"]),
                "output_path": to_ml_path(output_path)
            }
            
            try:
                resp = requests.post(f"{ml_url}/process_scene", json=payload)
                if resp.status_code == 200:
                    logger.success(f"ML Inference completed. Output: {output_path}")
                    resp_json = resp.json()
                    stats = resp_json.get("stats", {})
                    
                    shap_data = []
                    try:
                        exp_resp = requests.post(f"{ml_url}/explain", json={"features": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1]})
                        if exp_resp.status_code == 200:
                            shap_data = exp_resp.json().get("contributions", [])
                    except Exception as e:
                        logger.warning(f"Failed to fetch SHAP values: {e}")
                    
                    upload_to_db(
                        output_path, 
                        db_url, 
                        effective_aoi, 
                        scene_id=scene_id_override, 
                        acquisition_date=real_acquisition_date,
                        stats=stats,
                        shap_data=shap_data,
                        display_name=display_name
                    )
                else:
                    logger.error(f"ML Inference failed: {resp.status_code} - {resp.text}")
            except Exception as e:
                logger.error(f"Failed to contact ML service: {e}")

        logger.success("ETL Pipeline completed successfully for all AOIs!")
        update_job_status(engine, job_id, 'completed', 100)
        
    except Exception as e:
        logger.exception(f"ETL Pipeline failed: {e}")
        update_job_status(engine, job_id, 'failed')
        raise

if __name__ == "__main__":
    run_pipeline()
