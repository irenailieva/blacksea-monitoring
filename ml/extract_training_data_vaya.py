import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling
import numpy as np
import pandas as pd
from pathlib import Path

# -- CONFIGURATION --
# Paths to Lake Vaya Sentinel-2 Scene
BASE_DIR = Path("/app/data/inference/lake-vaya")
OUTPUT_CSV = Path("/app/dataset.csv")

# Bands
B2_PATH = BASE_DIR / "T35TNH_20230606T085559_B02_10m.jp2"
B3_PATH = BASE_DIR / "T35TNH_20230606T085559_B03_10m.jp2"
B4_PATH = BASE_DIR / "T35TNH_20230606T085559_B04_10m.jp2"
B8_PATH = BASE_DIR / "T35TNH_20230606T085559_B08_10m.jp2"
SCL_PATH = BASE_DIR / "T35TNH_20230606T085559_SCL_20m.jp2"

# ROI: Lake Vaya Bounding Box (WGS84 Lat/Lon)
MEAN_ROI_WGS84 = (27.3319, 42.4727, 27.4932, 42.5235)

import time

def extract_data():
    start_time = time.time()
    print(f"[{time.time()-start_time:.1f}s] --- Starting Lake Vaya Data Extraction (Force-Learning) ---")
    
    # 1. Determine Window
    window = None
    
    with rasterio.open(B2_PATH) as src:
        print(f"[{time.time()-start_time:.1f}s] Source CRS: {src.crs}")
        # Transform coordinates
        left, bottom, right, top = transform_bounds("EPSG:4326", src.crs, *MEAN_ROI_WGS84)
        window = from_bounds(left, bottom, right, top, transform=src.transform)
        print(f"[{time.time()-start_time:.1f}s] Read Window: {window}")

    # 2. Read Bands (Windowed)
    print(f"[{time.time()-start_time:.1f}s] Reading Bands (including SCL)...")
    with rasterio.open(B2_PATH) as src_b2, \
         rasterio.open(B3_PATH) as src_b3, \
         rasterio.open(B4_PATH) as src_b4, \
         rasterio.open(B8_PATH) as src_b8, \
         rasterio.open(SCL_PATH) as src_scl:
         
        b2 = src_b2.read(1, window=window).astype(float)
        print(f"[{time.time()-start_time:.1f}s] B2 Read. Shape: {b2.shape}")
        
        b3 = src_b3.read(1, window=window).astype(float)
        b4 = src_b4.read(1, window=window).astype(float)
        b8 = src_b8.read(1, window=window).astype(float)
        
        # SCL needs upscaling to match 10m window
        scl_window = from_bounds(left, bottom, right, top, transform=src_scl.transform)
        print(f"[{time.time()-start_time:.1f}s] Reading SCL. Window: {scl_window}")
        
        scl_raw = src_scl.read(
            1, 
            window=scl_window,
            out_shape=(b2.shape[0], b2.shape[1]), # Force shape match
            resampling=Resampling.nearest
        )
        print(f"[{time.time()-start_time:.1f}s] SCL Read. Shape: {scl_raw.shape}")

    # 3. Calculate Indices
    print(f"[{time.time()-start_time:.1f}s] Calculating Indices...")
    np.seterr(divide='ignore', invalid='ignore')
    
    # NDVI
    denom_ndvi = b8 + b4
    ndvi = np.where(denom_ndvi != 0, (b8 - b4) / denom_ndvi, -1.0)
    
    # NDWI
    denom_ndwi = b3 + b8
    ndwi = np.where(denom_ndwi != 0, (b3 - b8) / denom_ndwi, -1.0)
    
    # 4. Apply Force-Learning Rules
    print(" Applying Rules...")
    labels = np.full(ndvi.shape, -1, dtype=int)
    
    # TARGET: Class 2 (Deep Water) -> NDVI <= 0.0
    # Constraint: Water usually has SCL=6, but user logic focuses on NDVI.
    # We apply this first as a base layer for water areas.
    labels[ndvi <= 0.0] = 2
    
    # TARGET: Class 0 (Land/Abiotic) -> NDVI < 0.1 AND SCL == 5 (Non-vegetated)
    # This captures the "Red > Green" shores without explicit spectral check (relying on SCL).
    labels[(ndvi < 0.1) & (scl_raw == 5)] = 0
    
    # TARGET: Class 1 (Phytoplankton/Bloom) -> NDVI > 0.01 (Inside ROI)
    # "Force" this over others. 
    # If NDVI > 0.01, it's ALGAE (even if SCL thinks it's water or abiotic).
    # Overwrite previous labels.
    labels[ndvi > 0.01] = 1
    
    # 5. Sampling
    new_samples = []
    classes = [0, 1, 2]
    SAMPLES_PER_CLASS = 1000  # Updated to 1000
    
    print(" Sampling...")
    for c in classes:
        candidates = np.where(labels == c)
        n_candidates = len(candidates[0])
        print(f"  Class {c} Candidates: {n_candidates}")
        
        if n_candidates == 0:
            print(f"   Warning: No candidates for Class {c}")
            continue
            
        # Random sample
        n_samples = min(n_candidates, SAMPLES_PER_CLASS)
        indices = np.random.choice(n_candidates, n_samples, replace=False)
        selected_y = candidates[0][indices]
        selected_x = candidates[1][indices]
        
        for y, x in zip(selected_y, selected_x):
            new_samples.append({
                'class_id': c,
                'band_1': int(b2[y, x]),
                'band_2': int(b3[y, x]),
                'band_3': int(b4[y, x]),
                'band_4': int(b8[y, x]),
                'ndvi': round(float(ndvi[y, x]), 4),
                'ndwi': round(float(ndwi[y, x]), 4)
            })

    # 6. Save
    if not new_samples:
        print("No samples extracted.")
        return

    print(f"Extracted {len(new_samples)} total samples. Overwriting {OUTPUT_CSV}...")
    df = pd.DataFrame(new_samples)
    df.to_csv(OUTPUT_CSV, index=False)
    print("Done.")

if __name__ == "__main__":
    extract_data()
