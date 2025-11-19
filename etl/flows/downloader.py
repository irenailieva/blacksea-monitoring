import os
import numpy as np
import rasterio
from rasterio.transform import from_origin
from loguru import logger

def download_data(aoi: dict, time_range: dict, output_dir: str, mode: str = "mock") -> str:
    """
    Downloads Sentinel-2 data or generates a mock GeoTIFF.
    
    Args:
        aoi (dict): Area of Interest configuration.
        time_range (dict): Time range configuration.
        output_dir (str): Directory to save the downloaded file.
        mode (str): 'mock' or 'real'.
        
    Returns:
        str: Path to the downloaded/generated GeoTIFF file.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if mode == "mock":
        logger.info("Generating mock Sentinel-2 data...")
        filename = "mock_sentinel2.tif"
        filepath = os.path.join(output_dir, filename)
        
        # Generate dummy data: 4 bands (B2, B3, B4, B8) -> Blue, Green, Red, NIR
        # Size: 100x100 pixels
        width, height = 100, 100
        bands = 4
        
        # Random data simulating reflectance (0-10000)
        data = np.random.randint(0, 10000, size=(bands, height, width), dtype=rasterio.uint16)
        
        # Define transform (dummy coordinates based on AOI or default)
        # Using AOI bbox if available, else generic
        bbox = aoi.get("bbox", [27.85, 43.20, 27.95, 43.25])
        min_lon, min_lat = bbox[0], bbox[1]
        pixel_size = 0.0001 # Roughly 10m in degrees (very approx)
        transform = from_origin(min_lon, min_lat + (height * pixel_size), pixel_size, pixel_size)
        
        profile = {
            'driver': 'GTiff',
            'height': height,
            'width': width,
            'count': bands,
            'dtype': rasterio.uint16,
            'crs': 'EPSG:4326',
            'transform': transform
        }
        
        with rasterio.open(filepath, 'w', **profile) as dst:
            dst.write(data)
            dst.set_band_description(1, 'Blue')
            dst.set_band_description(2, 'Green')
            dst.set_band_description(3, 'Red')
            dst.set_band_description(4, 'NIR')
            
        logger.success(f"Mock data generated at {filepath}")
        return filepath
        
    else:
        # Placeholder for real API download (e.g., Copernicus Open Access Hub)
        logger.warning("Real download not implemented yet. Using mock data fallback.")
        return download_data(aoi, time_range, output_dir, mode="mock")
