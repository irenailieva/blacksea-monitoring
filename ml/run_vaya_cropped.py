import os
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling
from pathlib import Path
from model import load_model
from image_processor import process_scene
import utils
import numpy as np

# Global flag to control BOA offset correction
CORRECT_OFFSET = False

original_prepare_features = utils.prepare_features
def patched_prepare_features(blue, green, red, nir):
    b2_scaled = blue
    b3_scaled = green
    b4_scaled = red
    b8_scaled = nir
    
    if CORRECT_OFFSET:
        b2_scaled = np.clip(b2_scaled - 1000, 0, None)
        b3_scaled = np.clip(b3_scaled - 1000, 0, None)
        b4_scaled = np.clip(b4_scaled - 1000, 0, None)
        b8_scaled = np.clip(b8_scaled - 1000, 0, None)
        
    ndvi = utils.calculate_ndvi(b8_scaled, b4_scaled)
    ndwi = utils.calculate_ndwi(b3_scaled, b8_scaled)
    return np.column_stack([b2_scaled, b3_scaled, b4_scaled, b8_scaled, ndvi, ndwi])

import image_processor
image_processor.prepare_features = patched_prepare_features

# Vaya
MEAN_ROI_WGS84 = (27.3319, 42.4727, 27.4932, 42.5235)

def crop_band(input_path, output_path, bounds_wgs84, is_scl=False):
    with rasterio.open(input_path) as src:
        left, bottom, right, top = transform_bounds("EPSG:4326", src.crs, *bounds_wgs84)
        window = from_bounds(left, bottom, right, top, transform=src.transform)
        data = src.read(1, window=window)
        new_transform = src.window_transform(window)
        
        profile = src.profile.copy()
        profile.update({
            'driver': 'GTiff',
            'height': data.shape[0],
            'width': data.shape[1],
            'transform': new_transform,
            'compress': 'lzw'
        })
        
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(data, 1)

def run():
    base_dir = Path(r"C:\Users\irena\Downloads\vaya_lake_tiffs")
    artifacts_dir = Path(r"C:\TU\blacksea-monitoring\ml\artifacts")

    jp2_paths = {
        'b2': base_dir / "T35TNH_20230606T085559_B02_10m.jp2",
        'b3': base_dir / "T35TNH_20230606T085559_B03_10m.jp2",
        'b4': base_dir / "T35TNH_20230606T085559_B04_10m.jp2",
        'b8': base_dir / "T35TNH_20230606T085559_B08_10m.jp2",
        'scl': base_dir / "T35TNH_20230606T085559_SCL_20m.jp2"
    }

    cropped_paths = {}
    print("Checking cropped bands...")
    for key, path in jp2_paths.items():
        if not path.exists():
            print(f"Error: Missing {path}")
            return
        
        cropped_path = base_dir / f"cropped_vaya2_{key}.tif"
        if not cropped_path.exists():
            crop_band(str(path), str(cropped_path), MEAN_ROI_WGS84, is_scl=(key=='scl'))
        cropped_paths[key] = str(cropped_path)

    print("Loading ML model...")
    model = load_model(artifacts_dir)

    global CORRECT_OFFSET
    
    # Run WITHOUT correction
    print("\n--- Running WITHOUT correction ---")
    CORRECT_OFFSET = False
    output_uncorrected = base_dir / "vaya2_WITHOUT_correction.tif"
    process_scene(cropped_paths, str(output_uncorrected), model)
    
    # Run WITH correction
    print("\n--- Running WITH correction ---")
    CORRECT_OFFSET = True
    output_corrected = base_dir / "vaya2_WITH_correction.tif"
    process_scene(cropped_paths, str(output_corrected), model)
    
    print("\nDone!")

if __name__ == "__main__":
    run()
