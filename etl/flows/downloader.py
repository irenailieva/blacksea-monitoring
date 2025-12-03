import os
import numpy as np
import rasterio
from rasterio.transform import from_origin
from loguru import logger
import pystac_client
import odc.stac
import rioxarray

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
        
    elif mode == "real":
        logger.info("Searching for Sentinel-2 data via STAC...")
        
        STAC_URL = "https://earth-search.aws.element84.com/v1"
        
        bbox = aoi.get("bbox")
        if not bbox:
            raise ValueError("AOI must contain a 'bbox' [min_lon, min_lat, max_lon, max_lat]")
            
        start_date = time_range.get("start_date")
        end_date = time_range.get("end_date")
        datetime_query = f"{start_date}/{end_date}"
        
        try:
            client = pystac_client.Client.open(STAC_URL)
            
            search = client.search(
                collections=["sentinel-2-l2a"],
                bbox=bbox,
                datetime=datetime_query,
                max_items=1,
                query={"eo:cloud_cover": {"lt": 20}}
            )
            
            items = list(search.item_collection())
            
            if not items:
                logger.warning("No Sentinel-2 scenes found. Falling back to mock data.")
                return download_data(aoi, time_range, output_dir, mode="mock")
                
            logger.info(f"Found {len(items)} scenes. Downloading the first one...")
            
            # Load data (Blue, Green, Red, NIR)
            ds = odc.stac.load(
                items,
                bands=["blue", "green", "red", "nir"],
                bbox=bbox,
                crs="EPSG:4326",
                resolution=0.0001
            )
            
            if "time" in ds.dims:
                ds = ds.isel(time=0)
                
            filename = f"sentinel2_{items[0].id}.tif"
            filepath = os.path.join(output_dir, filename)
            
            # Convert to DataArray and save
            da = ds.to_array(dim="band")
            da.rio.to_raster(filepath)
            
            logger.success(f"Downloaded real data to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to download real data: {e}")
            logger.info("Falling back to mock data.")
            return download_data(aoi, time_range, output_dir, mode="mock")
