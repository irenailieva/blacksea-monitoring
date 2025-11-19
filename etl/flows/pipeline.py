from loguru import logger
from downloader import download_data
from index_generator import generate_index
from preprocessor import preprocess_raster
from uploader import upload_to_db

def run_pipeline():
    logger.info("Starting ETL pipeline")

    file = download_data(
        url="https://your-data-source/sample.tif",
        save_path="/app/sample.tif"
    )

    index = generate_index()
    arr = preprocess_raster(file)
    upload_to_db(arr, "postgresql://postgres:postgres@db:5432/postgres")

    logger.success("ETL Pipeline completed successfully!")

if __name__ == "__main__":
    run_pipeline()
