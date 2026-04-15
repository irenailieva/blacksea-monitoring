import rasterio
from rasterio.enums import Resampling
import numpy as np
import cv2
import os
import time
from utils import prepare_features
from PIL import Image


def process_scene(band_paths: dict, output_path: str, model):
    """
    Generates a water quality map from Sentinel-2 bands.
    
    Args:
        band_paths: Dict with keys 'b2', 'b3', 'b4', 'b8', 'scl'.
        output_path: Path to save the resulting TIF.
        model: Loaded WaterQualityModel instance.
    """
    
    b2_path = band_paths.get('b2')
    b3_path = band_paths.get('b3')
    b4_path = band_paths.get('b4')
    b8_path = band_paths.get('b8')
    scl_path = band_paths.get('scl')

    if not all([b2_path, b3_path, b4_path, b8_path, scl_path]):
        raise ValueError("Missing one or more required band paths.")

    # 🚀 SINGLE FILE MANUAL UPLOAD HANDLING
    # If the user uploaded a single RGB/Multispectral GeoTIFF, the backend passes the same file for all bands.
    is_single_file = (b2_path == b3_path == b4_path == b8_path == scl_path) and b2_path is not None
    
    if is_single_file:
        print(f"🔄 Processing single multi-band manual upload...")
        with rasterio.open(b2_path) as src:
            profile = src.profile.copy()
            profile.update(driver='GTiff', dtype=rasterio.uint8, count=1, nodata=255)
            
            has_nir = src.count >= 4
            
            with rasterio.open(output_path, 'w', **profile) as dst:
                for ji, window in src.block_windows(1):
                    # Band 1 -> Red (b4), Band 2 -> Green (b3), Band 3 -> Blue (b2)
                    b4 = src.read(1, window=window).astype('float32')
                    b3 = src.read(2, window=window).astype('float32') if src.count >= 2 else b4
                    b2 = src.read(3, window=window).astype('float32') if src.count >= 3 else b3
                    
                    if has_nir:
                        b8 = src.read(4, window=window).astype('float32')
                    else:
                        # Synthetic NIR fallback to Green ensures NDVI naturally isolates vegetation
                        # while avoiding false positives over bare soil.
                        b8 = b3

                    
                    target_mask = np.ones(b2.shape, dtype=bool) # No cloud mask available in RGB orthomosaics
                    result_block = np.full(b2.shape, 255, dtype=np.uint8)
                    
                    b2_water = b2[target_mask]
                    b3_water = b3[target_mask]
                    b4_water = b4[target_mask]
                    b8_water = b8[target_mask]
                    
                    X_water = prepare_features(b2_water, b3_water, b4_water, b8_water)
                    
                    if len(X_water) > 0:
                        mapped_pred = model.predict_batch(X_water)
                        result_block[target_mask] = mapped_pred
                        
                    dst.write(result_block, 1, window=window)
                    print(".", end="", flush=True)

        print(f"\n🎉 Single-file Map generated at {output_path}")
        return

    print(f"🔄 Processing multi-file Sentinel-2 scene...")

    # 1. Read SCL and Cloud Masking
    with rasterio.open(b2_path) as src_ref:
        target_height = src_ref.height
        target_width = src_ref.width
        ref_profile = src_ref.profile.copy()

    with rasterio.open(scl_path) as src_scl:
        # Upscale SCL to 10m (match B2)
        scl_full = src_scl.read(
            1,
            out_shape=(target_height, target_width), 
            resampling=Resampling.nearest 
        )

    # Cloud Masking (Classes: 3, 8, 9, 10)
    binary_cloud_mask = np.isin(scl_full, [3, 8, 9, 10]).astype(np.uint8)
    kernel = np.ones((15, 15), np.uint8) 
    dilated_cloud_mask = cv2.dilate(binary_cloud_mask, kernel, iterations=1)

    print("✅ Cloud mask generated.")

    # 2. Prepare Output Profile
    profile = ref_profile.copy()
    profile.update(
        driver='GTiff',
        dtype=rasterio.uint8, 
        count=1, 
        nodata=255
    )

    # 3. Process Blocks
    print(f"🌍 Generating map...")
    
    with rasterio.open(b2_path) as src_b2, \
         rasterio.open(b3_path) as src_b3, \
         rasterio.open(b4_path) as src_b4, \
         rasterio.open(b8_path) as src_b8, \
         rasterio.open(output_path, 'w', **profile) as dst:
        
        for ji, window in src_b2.block_windows(1):
            
            # Read Mask chunk
            row_start = window.row_off
            row_end = window.row_off + window.height
            col_start = window.col_off
            col_end = window.col_off + window.width
            
            scl_chunk = scl_full[row_start:row_end, col_start:col_end]
            cloud_chunk = dilated_cloud_mask[row_start:row_end, col_start:col_end]
            
            # Target Mask: Not Cloud (Let model decide on Water/Land/Veg)
            target_mask = (cloud_chunk == 0)
            
            if not target_mask.any():
                empty_block = np.full((window.height, window.width), 255, dtype=rasterio.uint8)
                dst.write(empty_block, 1, window=window)
                continue

            # Read Bands
            b2 = src_b2.read(1, window=window).astype('float32')
            b3 = src_b3.read(1, window=window).astype('float32')
            b4 = src_b4.read(1, window=window).astype('float32')
            b8 = src_b8.read(1, window=window).astype('float32')
            
            result_block = np.full(b2.shape, 255, dtype=np.uint8)
            
            # Extract water pixels
            b2_water = b2[target_mask]
            b3_water = b3[target_mask]
            b4_water = b4[target_mask]
            b8_water = b8[target_mask]
            
            # Prepare features with spectral indices: [B2, B3, B4, B8, NDVI, NDWI]
            X_water = prepare_features(b2_water, b3_water, b4_water, b8_water)
            
            if len(X_water) > 0:
                # Predict using the model
                # Model returns 10, 20, 30 directly
                mapped_pred = model.predict_batch(X_water)
                result_block[target_mask] = mapped_pred
            
            dst.write(result_block, 1, window=window)
            print(".", end="", flush=True)

    print(f"\n🎉 Map generated at {output_path}")
    
    # 🔥 BAKE HIGH-PERFORMANCE PNG
    png_path = output_path.replace(".tif", ".png")
    bake_png(output_path, png_path)

def bake_png(tif_path: str, png_path: str):
    """
    Converts a 1-channel classification TIFF into a 4-channel transparent RGBA PNG 
    using ROBUST range-mapping for floating-point and categorical artifacts.
    """
    print(f"📦 Baking high-performance PNG: {png_path}...")
    with rasterio.open(tif_path) as src:
        data = src.read(1).astype(np.float32)
        
        # Initialize RGBA (H, W, 4)
        h, w = data.shape
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        
        # Robust Range Mapping (Matches the most defensive frontend logic)
        # 1. Algae (Emerald Green #22c55e) - Priority 1
        algae_mask = ((data >= 1.5) & (data < 2.5)) | ((data >= 15) & (data < 25.5))
        rgba[algae_mask] = [34, 197, 94, 255]
        
        # 2. Sand/Land (Golden Yellow #facc15)
        sand_mask = ((data >= 0.5) & (data < 1.5)) | ((data >= 5) & (data < 15))
        rgba[sand_mask] = [250, 204, 21, 255]
        
        # 3. Water (Hydro Blue #0ea5e9)
        water_mask = ((data >= 2.5) & (data < 5.0)) | ((data >= 25.5) & (data < 45))
        rgba[water_mask] = [14, 165, 233, 255]

        img = Image.fromarray(rgba, 'RGBA')
        img.save(png_path, 'PNG')
        print(f"✅ PNG Baked successfully with {np.count_nonzero(algae_mask)} algae pixels.")
