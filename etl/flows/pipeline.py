import os
import sys
import yaml
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
        raw_file = download_data(
            aoi=config['aoi'],
            time_range=config['time'],
            output_dir=output_dir,
            mode=mode
        )
        
        # 2. Preprocess
        processed_file = preprocess_raster(raw_file)
        
        # 3. Generate Index (NDVI)
        ndvi_file = generate_index(processed_file, index_name='NDVI')
        
        # 4. Upload Metadata
        upload_to_db(raw_file, db_url, config['aoi'])
        upload_to_db(processed_file, db_url, config['aoi'])
        upload_to_db(ndvi_file, db_url, config['aoi'])
        
        logger.success("ETL Pipeline completed successfully!")
        
    except Exception as e:
        logger.exception(f"ETL Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    run_pipeline()
