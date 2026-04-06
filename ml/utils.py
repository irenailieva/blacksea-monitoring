"""
Helper utilities for calculating spectral indices.
"""
import numpy as np


def calculate_ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """
    Calculate NDVI (Normalized Difference Vegetation Index).
    
    Formula: NDVI = (NIR - Red) / (NIR + Red)
    
    Args:
        nir: Near-infrared band values (B8 for Sentinel-2)
        red: Red band values (B4 for Sentinel-2)
    
    Returns:
        NDVI values (range: -1 to 1)
    """
    denominator = nir + red
    return np.where(denominator != 0, (nir - red) / denominator, 0.0)


def calculate_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Calculate NDWI (Normalized Difference Water Index).
    
    Formula: NDWI = (Green - NIR) / (Green + NIR)
    
    Args:
        green: Green band values (B3 for Sentinel-2)
        nir: Near-infrared band values (B8 for Sentinel-2)
    
    Returns:
        NDWI values (range: -1 to 1)
    """
    denominator = green + nir
    return np.where(denominator != 0, (green - nir) / denominator, 0.0)


def prepare_features(blue: np.ndarray, green: np.ndarray, red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Prepare feature matrix with spectral bands and calculated indices.
    
    Features: [B2 (Blue), B3 (Green), B4 (Red), B8 (NIR), NDVI, NDWI]
    
    Args:
        blue: Blue band values (B2)
        green: Green band values (B3)
        red: Red band values (B4)
        nir: Near-infrared band values (B8)
    
    Returns:
        Feature matrix with shape (n_samples, 6)
    """
    # 🌡️ Auto-Intake Calibration Fix
    # The models were trained on Raw DN (0-10000) features for the spectral bands!
    # If the input is pre-scaled reflectance (0.0-1.0), we must MULTIPLY by 10,000.
    # If the input is already Raw DN, we leave it as is.
    data_max = np.nanmax(blue)
    scale_factor = 10000.0 if data_max <= 2.0 else 1.0
    
    b2_scaled = blue * scale_factor
    b3_scaled = green * scale_factor
    b4_scaled = red * scale_factor
    b8_scaled = nir * scale_factor

    ndvi = calculate_ndvi(b8_scaled, b4_scaled)
    ndwi = calculate_ndwi(b3_scaled, b8_scaled)
    
    return np.column_stack([b2_scaled, b3_scaled, b4_scaled, b8_scaled, ndvi, ndwi])
