import rasterio
from rasterio.enums import Resampling
import numpy as np
import cv2
import os
import time
from utils import prepare_features

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

    print(f"🔄 Processing scene...")

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
        nodata=255,      
        compress='lzw'
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
            
            # Target Mask: Water (SCL=6) AND Not Cloud
            target_mask = (scl_chunk == 6) & (cloud_chunk == 0)
            
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
