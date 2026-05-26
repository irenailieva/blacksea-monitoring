import rasterio
import numpy as np
from loguru import logger

# Функция за генериране на спектрални индекси (например NDVI) от предварително обработени растерни данни
def generate_index(raster_path: str, index_name: str = 'NDVI') -> str:
    """
    Generates a spectral index from the input raster.
    
    Args:
        raster_path (str): Path to the preprocessed raster.
        index_name (str): Name of the index to generate (default: NDVI).
        
    Returns:
        str: Path to the generated index GeoTIFF.
    """
    logger.info(f"Generating {index_name} for {raster_path}...")
    
    # Формиране на пътя за изходния файл, добавяйки името на индекса като суфикс
    output_path = raster_path.replace(".tif", f"_{index_name}.tif")
    
    # Отваряне на растерния файл за четене
    with rasterio.open(raster_path) as src:
        # Извличане на Червения (Red) и Близкия инфрачервен (NIR) канал.
        # В Sentinel-2 данните: B4 е Червеният канал (индекс 3), B8 е NIR (индекс 4).
        # Конвертират се във float32 за прецизни математически операции.
        
        red = src.read(3).astype('float32')
        nir = src.read(4).astype('float32')
        
        # Защита срещу деление на нула чрез добавяне на много малко число (epsilon)
        epsilon = 1e-10
        # Пресмятане на Нормализиран диференциален вегетационен индекс (NDVI):
        # NDVI = (NIR - Red) / (NIR + Red)
        ndvi = (nir - red) / (nir + red + epsilon)
        
        # Копиране на метаданните (profile) от оригиналния файл
        profile = src.profile
        # Обновяване на метаданните за новия файл с индекс
        # Тъй като индексът има само един канал (count=1) и е тип float32
        profile.update(
            dtype=rasterio.float32,
            count=1,
            driver='GTiff'
        )
        
        # Отваряне на нов файл за запис (write) с обновените метаданни
        with rasterio.open(output_path, 'w', **profile) as dst:
            # Запис на изчисления индекс като първи канал (band 1)
            dst.write(ndvi, 1)
            # Задаване на описание (име) на канала
            dst.set_band_description(1, index_name)
            
    logger.success(f"{index_name} generated at {output_path}")
    return output_path
