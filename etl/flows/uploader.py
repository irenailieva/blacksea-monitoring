from loguru import logger
from sqlalchemy import create_engine

def upload_to_db(data, conn_str):
    logger.info("Uploading to PostGIS...")
    engine = create_engine(conn_str)
    # примерен upload
    with engine.connect() as conn:
        conn.execute("SELECT 1;")
    logger.success("Upload complete")
