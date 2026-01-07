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
        logger.info("Generating mock Sentinel-2 data...")
        
        # 1. Generate Composite for existing ETL flow
        composite_filename = "mock_sentinel2.tif"
        composite_filepath = os.path.join(output_dir, composite_filename)
        
        width, height = 100, 100
        bands = 4
        
        # Random data
        data = np.random.randint(0, 5000, size=(bands, height, width), dtype=rasterio.uint16)
        
        bbox = aoi.get("bbox", [27.85, 43.20, 27.95, 43.25])
        min_lon, min_lat = bbox[0], bbox[1]
        pixel_size = 0.0001
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
        
        with rasterio.open(composite_filepath, 'w', **profile) as dst:
            dst.write(data)
            dst.set_band_description(1, 'Blue')
            dst.set_band_description(2, 'Green')
            dst.set_band_description(3, 'Red')
            dst.set_band_description(4, 'NIR')
            
        logger.success(f"Mock composite generated at {composite_filepath}")

        # 2. Generate Individual Bands for ML
        band_names = ['B02', 'B03', 'B04', 'B08', 'SCL']
        band_paths = {}
        
        for i, b_name in enumerate(band_names):
            fname = f"mock_{b_name}.tif"
            fpath = os.path.join(output_dir, fname)
            
            # SCL is band 5 in our loop logic here, but SCL has specific values
            if b_name == 'SCL':
                # SCL: 4=Veg, 5=Bare, 6=Water, etc.
                b_data = np.full((1, height, width), 6, dtype=rasterio.uint8) # All water
                dtype = rasterio.uint8
            else:
                b_data = np.random.randint(0, 5000, size=(1, height, width), dtype=rasterio.uint16)
                dtype = rasterio.uint16

            b_profile = profile.copy()
            b_profile.update(count=1, dtype=dtype)
            
            with rasterio.open(fpath, 'w', **b_profile) as dst:
                dst.write(b_data)
                
            band_paths[b_name.lower()] = fpath

        # Map SCL specifically to 'scl' key if needed, here we used 'scl' in loop but lower() handles it
        # Map B02 -> b2
        ml_band_paths = {
            'b2': band_paths['b02'],
            'b3': band_paths['b03'],
            'b4': band_paths['b04'],
            'b8': band_paths['b08'],
            'scl': band_paths['scl']
        }

        return {
            "composite": composite_filepath,
            "ml_bands": ml_band_paths
        }
        
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
            logger.info("Falling back to mock data.")
            return download_data(aoi, time_range, output_dir, mode="mock")
