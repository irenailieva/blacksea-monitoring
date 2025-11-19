import rasterio
import numpy as np
from loguru import logger

def generate_index(raster_path: str, index_name: str = 'NDVI') -> str:
    """
    Generates a spectral index from the input raster.
    
    Args:
        raster_path (str): Path to the preprocessed raster.
        index_name (str): Name of the index to generate (default: NDVI).
        
    Returns:
        str: Path to the generated index GeoTIFF.
    """
    logger.info(f"Generating {index_name} for {raster_path}...")
    
    output_path = raster_path.replace(".tif", f"_{index_name}.tif")
    
    with rasterio.open(raster_path) as src:
        # Assuming bands: 1=Blue, 2=Green, 3=Red, 4=NIR (based on our mock generator)
        # Real Sentinel-2: B4=Red, B8=NIR
        
        red = src.read(3).astype('float32')
        nir = src.read(4).astype('float32')
        
        # Avoid division by zero
        epsilon = 1e-10
        ndvi = (nir - red) / (nir + red + epsilon)
        
        profile = src.profile
        profile.update(
            dtype=rasterio.float32,
            count=1,
            driver='GTiff'
        )
        
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(ndvi, 1)
            dst.set_band_description(1, index_name)
            
    logger.success(f"{index_name} generated at {output_path}")
    return output_path
