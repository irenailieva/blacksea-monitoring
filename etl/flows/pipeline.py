import os
import sys
import yaml
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

from sqlalchemy import create_engine
from backend.app.models import Base


def load_config():
    # Try to find config.yml in parent directory (when running from flows/)
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yml")
    if not os.path.exists(config_path):
        # Fallback to current directory
        config_path = "config.yml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def run_pipeline():
    logger.info("Starting ETL pipeline")
    
    config = load_config()
    
    # Get settings from env or config
    mode = os.getenv("ETL_MODE", "mock")
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

    try:
        # 1. Download
        download_result = download_data(
            aoi=config['aoi'],
            time_range=config['time'],
            output_dir=output_dir,
            mode=mode
        )
        
        raw_file = download_result["composite"]
        ml_bands = download_result["ml_bands"]
        
        # 2. Preprocess
        processed_file = preprocess_raster(raw_file)
        
        # 3. Generate Index (NDVI)
        ndvi_file = generate_index(processed_file, index_name='NDVI')
        
        # 4. Upload Metadata
        upload_to_db(raw_file, db_url, config['aoi'])
        upload_to_db(processed_file, db_url, config['aoi'])
        upload_to_db(ndvi_file, db_url, config['aoi'])
        
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
                upload_to_db(output_path, db_url, config['aoi'])
            else:
                logger.error(f"ML Inference failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"Failed to contact ML service: {e}")
        
        logger.success("ETL Pipeline completed successfully!")
        
    except Exception as e:
        logger.exception(f"ETL Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    run_pipeline()
