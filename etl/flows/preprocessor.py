import rasterio
import numpy as np
from loguru import logger

# Функция за предварителна обработка (preprocessing) на растерно изображение
def preprocess_raster(input_path: str) -> str:
    """
    Preprocesses the input raster.
    Currently implements basic normalization or pass-through.
    
    Args:
        input_path (str): Path to the input GeoTIFF.
        
    Returns:
        str: Path to the preprocessed GeoTIFF.
    """
    logger.info(f"Preprocessing {input_path}...")
    
    # В момента функцията създава копие на изображението.
    # В реални сценарии тук се прилагат алгоритми за атмосферна корекция (напр. Sen2Cor)
    # или маскиране на облаци.
    
    # Дефиниране на пътя за изходния (обработен) файл
    output_path = input_path.replace(".tif", "_processed.tif")
    
    # Отваряне на суровия растерен файл
    with rasterio.open(input_path) as src:
        # Извличане на метаданните (георефериране, брой канали, тип данни)
        profile = src.profile
        # Изчитане на всички пиксели в паметта
        data = src.read()
        
        # Тук би могла да се приложи нормализация на стойностите до обхват 0-1 (float32).
        # Засега запазваме оригиналния формат (най-често uint16), за да пестим място 
        # и да запазим оригиналната радиометрична резолюция.
        
        # Отваряне на новия файл и записване на обработените данни
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(data)
            
            # Копиране на описанията (имената) на всеки канал от оригиналния към новия файл
            for i in range(1, src.count + 1):
                dst.set_band_description(i, src.descriptions[i-1])
                
    logger.success(f"Preprocessing complete. Saved to {output_path}")
    return output_path
