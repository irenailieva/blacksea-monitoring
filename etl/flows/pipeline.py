import os
import yaml
from dotenv import load_dotenv
from loguru import logger
from downloader import download_data
from index_generator import generate_index
from preprocessor import preprocess_raster
from uploader import upload_to_db

# Load env vars
load_dotenv()

def load_config():
    with open("config.yml", "r") as f:
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
