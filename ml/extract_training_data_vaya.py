import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
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

# ROI: Lake Vaya Bounding Box (WGS84 Lat/Lon)
# (West, South, East, North)
MEAN_ROI_WGS84 = (27.3319, 42.4727, 27.4932, 42.5235)

def extract_data():
    print("--- Starting Lake Vaya Data Extraction ---")
    
    # 1. Determine Window
    window = None
    
    with rasterio.open(B2_PATH) as src:
        print(f"Source CRS: {src.crs}")
        
        # Transform coordinates from WGS84 (4326) to the Image's CRS
        print(f"Transforming ROI {MEAN_ROI_WGS84} to Image CRS...")
        left, bottom, right, top = transform_bounds(
            "EPSG:4326", 
            src.crs, 
            *MEAN_ROI_WGS84
        )
        print(f"Projected Bounds: ({left:.2f}, {bottom:.2f}, {right:.2f}, {top:.2f})")
        
        # Create the window for reading
        window = from_bounds(left, bottom, right, top, transform=src.transform)
        print(f"Read Window: {window}")

    # 2. Read Bands (Windowed)
    print("Reading Bands...")
    with rasterio.open(B2_PATH) as src_b2, \
         rasterio.open(B3_PATH) as src_b3, \
         rasterio.open(B4_PATH) as src_b4, \
         rasterio.open(B8_PATH) as src_b8:
         
        b2 = src_b2.read(1, window=window).astype(float)
        b3 = src_b3.read(1, window=window).astype(float)
        b4 = src_b4.read(1, window=window).astype(float)
        b8 = src_b8.read(1, window=window).astype(float)

    # 3. Calculate Indices
    print("Calculating Indices...")
    np.seterr(divide='ignore', invalid='ignore')
    
    # NDVI = (NIR - Red) / (NIR + Red)
    denom_ndvi = b8 + b4
    ndvi = np.where(denom_ndvi != 0, (b8 - b4) / denom_ndvi, -1.0)
    
    # NDWI = (Green - NIR) / (Green + NIR)
    denom_ndwi = b3 + b8
    ndwi = np.where(denom_ndwi != 0, (b3 - b8) / denom_ndwi, -1.0)
    
    # 4. Apply Classification Rules (Active Learning)
    print(" Applying Rules...")
    
    # Masks
    # C1 (Veg/Algae): (NDVI > 0.05) AND (Green > Red)
    mask_c1 = (ndvi > 0.05) & (b3 > b4)
    
    # C0 (Abiotic): (NDVI < 0.15) AND (Red >= Green)
    mask_c0 = (ndvi < 0.15) & (b4 >= b3)
    
    # C2 (Deep Water): NDVI <= 0.0
    # Note: C2 takes precedence or we handle intersection?
    # Usually Deep Water satisfies NDVI <= 0.
    # If a pixel matches C2 (NDVI<=0) and C0 (<0.15, R>=G), it's ambiguous.
    # But Deep water usually has Green > Red (if clear). If Red >= Green + Low NDVI, likely Turbid/Abiotic.
    # So we enforce:
    # C2 Strict: NDVI <= 0.0 AND Green > Red ?? User rule was just "NDVI <= 0.0".
    # User Rules:
    # 1. C1: NDVI > 0.05 AND G > R
    # 2. C0: NDVI < 0.15 AND R >= G
    # 3. C2: NDVI <= 0.0
    # Process C2 first to capture "Deep Water", or treat C0/C1 as specific overrides?
    # "Class 2 (Deep Water): Goal: Clean, deep water."
    # Let's enforce the "Green > Red" implicitly for Clean Water or explicitly exclude C0.
    # Actually, if we follow user rules literally:
    # Pixel A: NDVI -0.1, G 1000, R 800 (Green > Red).
    #   C1: False.
    #   C0: False (R < G).
    #   C2: True (-0.1 <= 0). -> Class 2 (Correct).
    # Pixel B: NDVI -0.1, G 800, R 1000 (Red > Green, Turbid).
    #   C1: False.
    #   C0: True (NDVI < 0.15, R >= G).
    #   C2: True (NDVI <= 0).
    #   Result: It fits both Abiotic and Deep Water rules.
    #   "Class 0... Capture sand, rocks... and turbid sediment water".
    #   So Pixel B should be Class 0.
    #   Therefore, C0 MUST take precedence over C2 if they overlap.
    
    # Refined Logic Step:
    # Initialize labels with -1
    labels = np.full(ndvi.shape, -1, dtype=int)
    
    # Apply C2 (Base Water)
    labels[ndvi <= 0.0] = 2
    
    # Apply C0 (Abiotic / Turbid) - This overwrites C2 if "Red >= Green"
    labels[(ndvi < 0.15) & (b4 >= b3)] = 0
    
    # Apply C1 (Veg) - High confidence
    labels[(ndvi > 0.05) & (b3 > b4)] = 1
    
    # 5. Sampling
    new_samples = []
    classes = [0, 1, 2]
    SAMPLES_PER_CLASS = 500
    
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
                'band_2': int(b3[y, x]), # Green
                'band_3': int(b4[y, x]), # Red
                'band_4': int(b8[y, x]), # NIR
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
