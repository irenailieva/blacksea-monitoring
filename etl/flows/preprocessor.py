from loguru import logger
import rasterio

def preprocess_raster(file_path):
    logger.info(f"Reading raster {file_path}")
    with rasterio.open(file_path) as src:
        arr = src.read(1)
    logger.success("Raster loaded")
    return arr
