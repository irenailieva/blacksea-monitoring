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
    # ML моделите са обучени върху „сурови" стойности (Raw DN) в диапазон 0-10000.
    #
    # odc.stac зарежда Sentinel-2 L2A данни (ESA Processing Baseline 4.0+) с автоматично
    # приложен BOA offset: reflectance = DN * 0.0001 + (-0.1)
    # Тоест тъмните пиксели (вода, сенки) с DN~700 получават: 700*0.0001 - 0.1 = -0.03
    # (отрицателна стойност!), а след умножение по 10000 стават -300 — напълно извън
    # разпределението, на което е учен моделът.
    #
    # Решение: ако данните изглеждат скалирани (max <= 2.0), те са BOA reflectance.
    # Добавяме обратно BOA_ADD_OFFSET (+0.1) преди умножението, за да се върнат
    # в диапазона на DN стойностите, очаквани от модела.
    BOA_ADD_OFFSET = 0.1   # ESA Sentinel-2 L2A Processing Baseline 4.0+ offset (-0.1 applied by odc.stac)
    data_max = np.nanmax(blue)

    if data_max <= 2.0:
        # Данните са BOA reflectance с вграден offset — обръщаме го и скалираме до DN
        scale_factor = 10000.0
        b2_scaled = (blue  + BOA_ADD_OFFSET) * scale_factor
        b3_scaled = (green + BOA_ADD_OFFSET) * scale_factor
        b4_scaled = (red   + BOA_ADD_OFFSET) * scale_factor
        b8_scaled = (nir   + BOA_ADD_OFFSET) * scale_factor
    else:
        # Данните вече са в DN диапазон (0-10000) — използваме директно
        b2_scaled = blue
        b3_scaled = green
        b4_scaled = red
        b8_scaled = nir

    # Изчисляване на индексите върху вече калибрираните данни
    ndvi = calculate_ndvi(b8_scaled, b4_scaled)
    ndwi = calculate_ndwi(b3_scaled, b8_scaled)
    
    # Обединяване на всички колони (column_stack ги "залепва" една до друга)
    return np.column_stack([b2_scaled, b3_scaled, b4_scaled, b8_scaled, ndvi, ndwi])
