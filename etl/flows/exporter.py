import os
import glob
import re
import pandas as pd
import rasterio
import numpy as np
from pathlib import Path
from loguru import logger

def extract_date_from_filename(filename: str) -> str:
    """
    Extracts date from filename. 
    Expects format like sentinel2_{id}.tif or mock_sentinel2.tif
    For mock data, returns a default date.
    For real data (if filename contains date), extracts it.
    Otherwise returns a placeholder.
    """
    # Simple regex for YYYY-MM-DD or YYYYMMDD if present
    match = re.search(r"(\d{4}[-_]\d{2}[-_]\d{2})", filename)
    if match:
        return match.group(1)
    
    # Fallback for mock or unknown
    return "2024-01-01"

def export_to_csv(input_dir: str, output_csv: str):
    """
    Reads all .tif files in input_dir, flattens them, and appends to a CSV.
    """
    logger.info(f"Exporting data from {input_dir} to {output_csv}...")
    
    tif_files = glob.glob(os.path.join(input_dir, "*.tif"))
    if not tif_files:
        logger.warning(f"No .tif files found in {input_dir}")
        return

    all_data = []

    for tif_path in tif_files:
        filename = os.path.basename(tif_path)
        # Skip intermediate processed files if needed, or just use them. 
        # For now, we take everything that looks like an image.
        if "processed" in filename: 
            # If we have both raw and processed, avoid duplication.
            # Let's prefer processed if available, or just take everything if distinct.
            # Assuming we want the final state.
            pass

        date_str = extract_date_from_filename(filename)
        
        with rasterio.open(tif_path) as src:
            # Expecting 4 bands: Blue, Green, Red, NIR
            if src.count < 4:
                logger.warning(f"Skipping {filename}: expected at least 4 bands, got {src.count}")
                continue

            # Read all bands
            # data shape: (bands, height, width)
            data = src.read()
            
            bands, height, width = data.shape
            
            # Create meshgrid for x, y coordinates
            # x is column (width), y is row (height)
            cols, rows = np.meshgrid(np.arange(width), np.arange(height))
            
            # Flatten everything
            # We want rows like: date, x, y, blue, green, red, nir, target
            
            # Flatten arrays
            rows_flat = rows.flatten()
            cols_flat = cols.flatten()
            
            b1 = data[0].flatten() # Blue
            b2 = data[1].flatten() # Green
            b3 = data[2].flatten() # Red
            b4 = data[3].flatten() # NIR
            
            # Create a DataFrame for this image
            df_img = pd.DataFrame({
                'date': date_str,
                'x': cols_flat,
                'y': rows_flat,
                'blue': b1,
                'green': b2,
                'red': b3,
                'nir': b4,
                'target': 0.0 # Placeholder
            })
            
            all_data.append(df_img)
            logger.info(f"Processed {filename}: {len(df_img)} pixels")

    if not all_data:
        logger.warning("No data extracted.")
        return

    final_df = pd.concat(all_data, ignore_index=True)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    final_df.to_csv(output_csv, index=False)
    logger.success(f"Successfully exported {len(final_df)} rows to {output_csv}")

if __name__ == "__main__":
    # Test run
    # Assuming script is run from project root (e.g. docker compose run etl ...)
    IN_DIR = "etl/out" 
    OUT_CSV = "ml/data/train.csv"
    
    # Check if we are inside the container at /app
    if os.path.exists("/app/out"):
        IN_DIR = "/app/out"
        OUT_CSV = "/app/ml/data/train.csv"
        
    export_to_csv(IN_DIR, OUT_CSV)
