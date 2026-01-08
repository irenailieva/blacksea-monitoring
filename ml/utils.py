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
    ndvi = calculate_ndvi(nir, red)
    ndwi = calculate_ndwi(green, nir)
    
    return np.column_stack([blue, green, red, nir, ndvi, ndwi])
