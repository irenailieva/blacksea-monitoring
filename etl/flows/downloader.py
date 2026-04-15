import os
import numpy as np
import rasterio
from rasterio.transform import from_origin
from loguru import logger
import pystac_client
import odc.stac
import rioxarray

def download_data(aoi: dict, time_range: dict, output_dir: str, mode: str = "mock") -> dict:
    """
    Downloads Sentinel-2 data or generates a mock GeoTIFF.
    
    Args:
        aoi (dict): Area of Interest configuration.
        time_range (dict): Time range configuration.
        output_dir (str): Directory to save the downloaded file.
        mode (str): 'mock' or 'real'.
        
    Returns:
        dict: Dictionary containing 'composite' path and 'ml_bands' dict.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if mode == "mock":
        raise NotImplementedError("Mock mode has been disabled. Please use 'real' mode.")
        
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
                logger.warning("No Sentinel-2 scenes found for this AOI and date range.")
                raise FileNotFoundError("No Satellite scenes found. Check your search parameters.")
                
            logger.info(f"Found {len(items)} scenes. Downloading the first one...")
            
            # Load Composite data for Dashboard (Blue, Green, Red, NIR)
            ds = odc.stac.load(
                items,
                bands=["blue", "green", "red", "nir"],
                bbox=bbox,
                crs="EPSG:4326",
                resolution=0.0001
            )
            
            if "time" in ds.dims:
                ds = ds.isel(time=0)
                
            composite_filename = f"sentinel2_{items[0].id}.tif"
            composite_filepath = os.path.join(output_dir, composite_filename)
            
            # Convert to DataArray and save
            da = ds.to_array(dim="band")
            da.rio.to_raster(composite_filepath)
            
            # --- Load Individual Bands for ML (including SCL) ---
            # We load them separately or extracting from a larger fetch to ensure we get SCL
            ds_ml = odc.stac.load(
                items,
                bands=["blue", "green", "red", "nir", "scl"],
                bbox=bbox,
                crs="EPSG:4326",
                resolution=0.0001
            )
            if "time" in ds_ml.dims:
                ds_ml = ds_ml.isel(time=0)

            ml_band_paths = {}
            band_map = {
                "blue": "b2", "green": "b3", "red": "b4", "nir": "b8", "scl": "scl"
            }

            for stac_name, ml_name in band_map.items():
                band_filename = f"sentinel2_{items[0].id}_{ml_name}.tif"
                band_filepath = os.path.join(output_dir, band_filename)
                
                # Select single band
                # ds_ml[stac_name] is the DataArray for that band
                ds_ml[stac_name].rio.to_raster(band_filepath)
                ml_band_paths[ml_name] = band_filepath
            
            logger.success(f"Downloaded real data to {composite_filepath}")
            return {
                "composite": composite_filepath,
                "ml_bands": ml_band_paths
            }
            
        except Exception as e:
            logger.error(f"Failed to download real data: {e}")
            raise
