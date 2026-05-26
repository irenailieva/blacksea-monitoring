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
    # 🌡️ Автоматична калибрация на входа (Auto-Intake Calibration)
    # ML моделите са обучени върху "сурови" стойности (Raw DN), които 
    # за Sentinel-2 обикновено са в диапазона 0-10000.
    # Ако подаденият масив вече е скалиран (напр. от 0.0 до 1.0 като отражателна способност),
    # ние трябва да го умножим по 10000, за да съвпадне с разпределението, на което е учен моделът.
    data_max = np.nanmax(blue)
    scale_factor = 10000.0 if data_max <= 2.0 else 1.0
    
    # Прилагане на калибриращия фактор
    b2_scaled = blue * scale_factor
    b3_scaled = green * scale_factor
    b4_scaled = red * scale_factor
    b8_scaled = nir * scale_factor

    # Изчисляване на индексите върху вече калибрираните данни
    ndvi = calculate_ndvi(b8_scaled, b4_scaled)
    ndwi = calculate_ndwi(b3_scaled, b8_scaled)
    
    # Обединяване на всички колони (column_stack ги "залепва" една до друга)
    return np.column_stack([b2_scaled, b3_scaled, b4_scaled, b8_scaled, ndvi, ndwi])
