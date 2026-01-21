import rasterio
from rasterio.enums import Resampling
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from pathlib import Path

# Paths
BASE_DIR = Path("/app/data/inference/lake-vaya")
INPUT_TIF = BASE_DIR / "output_classification.tif"
SCL_PATH = BASE_DIR / "T35TNH_20230606T085559_SCL_20m.jp2"
OUTPUT_PNG = BASE_DIR / "final_vaya_map.png"

def apply_mask():
    print("--- Applying Land Mask to Lake Vaya Map ---")
    
    # 1. Read Classification Result (10m)
    with rasterio.open(INPUT_TIF) as src_tif:
        print(f"Reading Classification Map: {src_tif.shape}")
        classification = src_tif.read(1)
        profile = src_tif.profile
        
    # 2. Read SCL (20m) and Upscale
    print("Reading and Upscaling SCL Mask...")
    with rasterio.open(SCL_PATH) as src_scl:
        scl = src_scl.read(
            1,
            out_shape=(src_tif.height, src_tif.width),
            resampling=Resampling.nearest
        )
        
    # 3. Create Mask
    # SCL 4 = Vegetation, 5 = Bare Soils
    # We want to mask these out to remove false positives on land
    land_mask = (scl == 4) | (scl == 5)
    print(f"Masked Pixels: {np.sum(land_mask)} / {land_mask.size} ({np.sum(land_mask)/land_mask.size:.2%} of scene)")
    
    # 4. Visualization Logic
    # Classes: 10 (Abiotic), 20 (Veg), 30 (Water)
    # Plus 0/255 for NoData
    
    # Create RGBA array
    # Shape: (H, W, 4)
    height, width = classification.shape
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    
    # Define Colors (R, G, B, A)
    # Class 10: Abiotic (Grey/Brown) - e.g. Rocks/Sand inside water or shore
    c10 = [160, 140, 120, 255]
    # Class 20: Vegetation (Vibrant Green)
    c20 = [0, 255, 0, 255]
    # Class 30: Deep Water (Blue)
    c30 = [0, 100, 255, 255]
    
    # Apply Colors
    rgba[classification == 10] = c10
    rgba[classification == 20] = c20
    rgba[classification == 30] = c30
    
    # Apply Land Mask (Set Alpha to 0)
    rgba[land_mask, 3] = 0
    
    # Also mask NoData (255)
    rgba[classification == 255, 3] = 0

    # 5. Save
    print(f"Saving to {OUTPUT_PNG}...")
    plt.imsave(OUTPUT_PNG, rgba)
    print("Done.")

if __name__ == "__main__":
    apply_mask()
