import rasterio
import numpy as np
from loguru import logger

def preprocess_raster(input_path: str) -> str:
    """
    Preprocesses the input raster.
    Currently implements basic normalization or pass-through.
    
    Args:
        input_path (str): Path to the input GeoTIFF.
        
    Returns:
        str: Path to the preprocessed GeoTIFF.
    """
    logger.info(f"Preprocessing {input_path}...")
    
    # For now, we'll just create a copy or perform a simple check.
    # In a real scenario, this would handle atmospheric correction (Sen2Cor) or cloud masking.
    
    output_path = input_path.replace(".tif", "_processed.tif")
    
    with rasterio.open(input_path) as src:
        profile = src.profile
        data = src.read()
        
        # Example: Simple normalization to 0-1 range (float32) if needed, 
        # but usually we keep uint16 for storage efficiency until analysis.
        # Let's just pass through for now but ensure integrity.
        
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(data)
            # Copy band descriptions
            for i in range(1, src.count + 1):
                dst.set_band_description(i, src.descriptions[i-1])
                
    logger.success(f"Preprocessing complete. Saved to {output_path}")
    return output_path
