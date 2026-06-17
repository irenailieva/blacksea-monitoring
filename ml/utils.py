"""
Помощни функции (Utils) за изчисляване на спектрални индекси и
предварителна подготовка на данните (Feature Engineering).
"""
import numpy as np

def calculate_ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """
    Изчислява NDVI (Нормализиран диференциален вегетационен индекс).
    Използва се за засичане на жива растителност (вкл. водорасли).
    
    Формула: NDVI = (NIR - Red) / (NIR + Red)
    
    Аргументи:
        nir: Стойности от близкия инфрачервен канал (B8 за Sentinel-2)
        red: Стойности от червения канал (B4 за Sentinel-2)
    
    Връща:
        NDVI масив със стойности от -1 до 1.
    """
    denominator = nir + red
    # Използваме np.where за избягване на деление на нула
    return np.where(denominator != 0, (nir - red) / denominator, 0.0)

def calculate_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Изчислява NDWI (Нормализиран диференциален воден индекс).
    Използва се за ясно разграничаване на водни басейни от суша.
    
    Формула: NDWI = (Green - NIR) / (Green + NIR)
    
    Аргументи:
        green: Стойности от зеления канал (B3 за Sentinel-2)
        nir: Стойности от близкия инфрачервен канал (B8 за Sentinel-2)
    
    Връща:
        NDWI масив със стойности от -1 до 1.
    """
    denominator = green + nir
    return np.where(denominator != 0, (green - nir) / denominator, 0.0)

def prepare_features(blue: np.ndarray, green: np.ndarray, red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Подготвя финалната матрица с характеристики (features), комбинирайки 
    основните спектрални канали и изчислените индекси.
    
    Ред на характеристиките: [B2 (Син), B3 (Зелен), B4 (Червен), B8 (NIR), NDVI, NDWI]
    
    Аргументи:
        blue: Стойности от синия канал (B2)
        green: Стойности от зеления канал (B3)
        red: Стойности от червения канал (B4)
        nir: Стойности от близкия инфрачервен канал (B8)
    
    Връща:
        Двумерна матрица с форма (брой_примери, 6)
    """
    data_max = np.nanmax(blue)
    valid_blue = blue[blue > 0]
    # Use median instead of min because min can be pulled down by overcorrected dark pixels
    data_median = np.nanmedian(valid_blue) if len(valid_blue) > 0 else 0

    if data_max <= 2.0:
        # odc.stac Sentinel-2 L2A data with auto-applied offset: reflectance = (DN - 1000) / 10000
        scale_factor = 10000.0
        b2_scaled = np.clip(blue * scale_factor, 0, None)
        b3_scaled = np.clip(green * scale_factor, 0, None)
        b4_scaled = np.clip(red * scale_factor, 0, None)
        b8_scaled = np.clip(nir * scale_factor, 0, None)
    elif data_median >= 800:
        # Raw JP2 data. Contains ESA Baseline 4.0+ offset (+1000). We must subtract it.
        # Check median >= 800 because water reflectance is typically ~100-300, plus 1000 = 1100-1300.
        b2_scaled = np.clip(blue - 1000.0, 0, None)
        b3_scaled = np.clip(green - 1000.0, 0, None)
        b4_scaled = np.clip(red - 1000.0, 0, None)
        b8_scaled = np.clip(nir - 1000.0, 0, None)
    else:
        # Data is 0-10000 but does NOT have the offset (e.g. from Planetary Computer)
        b2_scaled = blue.copy()
        b3_scaled = green.copy()
        b4_scaled = red.copy()
        b8_scaled = nir.copy()

    # Изчисляване на индексите върху вече калибрираните данни
    ndvi = calculate_ndvi(b8_scaled, b4_scaled)
    ndwi = calculate_ndwi(b3_scaled, b8_scaled)
    
    # Обединяване на всички колони (column_stack ги "залепва" една до друга)
    return np.column_stack([b2_scaled, b3_scaled, b4_scaled, b8_scaled, ndvi, ndwi])
