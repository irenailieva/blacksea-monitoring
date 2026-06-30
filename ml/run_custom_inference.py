import os
from pathlib import Path
import numpy as np

# We'll patch utils.prepare_features to support with/without correction
import utils
original_prepare_features = utils.prepare_features

CORRECT_OFFSET = False

def patched_prepare_features(blue, green, red, nir):
    # Call original first to see what it does
    # Since the tiffs are raw DN, data_max > 2.0, so the original just returns blue, green, etc.
    # We'll just do it manually here.
    
    b2_scaled = blue
    b3_scaled = green
    b4_scaled = red
    b8_scaled = nir
    
    if CORRECT_OFFSET:
        # The offset is +1000 in DN for Baseline 4.0+. To correct it, we subtract 1000.
        b2_scaled = np.clip(b2_scaled - 1000, 0, None)
        b3_scaled = np.clip(b3_scaled - 1000, 0, None)
        b4_scaled = np.clip(b4_scaled - 1000, 0, None)
        b8_scaled = np.clip(b8_scaled - 1000, 0, None)
        
    ndvi = utils.calculate_ndvi(b8_scaled, b4_scaled)
    ndwi = utils.calculate_ndwi(b3_scaled, b8_scaled)
    
    return np.column_stack([b2_scaled, b3_scaled, b4_scaled, b8_scaled, ndvi, ndwi])

utils.prepare_features = patched_prepare_features

from model import load_model
from image_processor import process_scene

def run_inference():
    base_dir = Path(r"C:\Users\irena\Downloads\vaya_lake_tiffs")
    artifacts_dir = Path(r"C:\TU\blacksea-monitoring\ml\artifacts")

    # Map the files based on the directory contents
    band_paths = {
        'b2': str(base_dir / "T35TNH_20230606T085559_B02_10m.jp2"),
        'b3': str(base_dir / "T35TNH_20230606T085559_B03_10m.jp2"),
        'b4': str(base_dir / "T35TNH_20230606T085559_B04_10m.jp2"),
        'b8': str(base_dir / "T35TNH_20230606T085559_B08_10m.jp2"),
        'scl': str(base_dir / "T35TNH_20230606T085559_SCL_20m.jp2")
    }

    print("Checking files...")
    for b, p in band_paths.items():
        if not os.path.exists(p):
            print(f"Missing file: {p}")
            return
            
    print("Loading models...")
    model = load_model(artifacts_dir)

    global CORRECT_OFFSET
    
    # 1. Run WITHOUT correction
    print("--- Running WITHOUT correction ---")
    CORRECT_OFFSET = False
    output_uncorrected = base_dir / "classification_result_WITHOUT_correction.tif"
    process_scene(band_paths, str(output_uncorrected), model)
    print(f"Saved to {output_uncorrected}")
    
    # 2. Run WITH correction
    print("--- Running WITH correction ---")
    CORRECT_OFFSET = True
    output_corrected = base_dir / "classification_result_WITH_correction.tif"
    process_scene(band_paths, str(output_corrected), model)
    print(f"Saved to {output_corrected}")

if __name__ == "__main__":
    run_inference()
