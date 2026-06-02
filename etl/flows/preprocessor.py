import os
import rasterio
import numpy as np
from loguru import logger

# Импортиране на ACOLITE модула за атмосферна корекция
from flows.acolite_corrector import apply_acolite_correction, is_available as acolite_available

# ==============================================================================
# PREPROCESSOR.PY — Предварителна обработка и атмосферна корекция
# Прилага ACOLITE Dark Spectrum Fitting (DSF) корекция върху L1C данни
# от Sentinel-2. При липса на ACOLITE или L1C данни, се извършва базова
# обработка (passthrough) на L2A данните.
# ==============================================================================

def preprocess_raster(input_path: str, aoi_bbox: list = None, l1c_path: str = None) -> str:
    """
    Предварителна обработка на растерно изображение с ACOLITE атмосферна корекция.
    
    Функцията се опитва да приложи ACOLITE DSF корекция върху L1C данните.
    Ако ACOLITE не е наличен или L1C данните липсват, се извършва базова
    обработка (копиране с нормализация) на L2A данните.
    
    Args:
        input_path (str): Път до входния GeoTIFF (L2A composite).
        aoi_bbox (list): Ограничителна рамка [minLon, minLat, maxLon, maxLat].
        l1c_path (str): Път до L1C данните за ACOLITE (GeoTIFF или .SAFE директория).
        
    Returns:
        str: Път до обработения GeoTIFF файл.
    """
    logger.info(f"Предварителна обработка на: {input_path}")
    
    output_dir = os.path.dirname(input_path)
    
    # ── Стъпка 1: Опит за ACOLITE атмосферна корекция ──
    if acolite_available() and l1c_path and os.path.exists(l1c_path):
        logger.info("Прилагане на ACOLITE атмосферна корекция (Dark Spectrum Fitting)...")
        
        try:
            # Изпълнение на ACOLITE DSF корекция
            corrected_bands = apply_acolite_correction(
                input_path=l1c_path,
                output_dir=output_dir,
                aoi_bbox=aoi_bbox
            )
            
            if corrected_bands:
                # Създаване на композитен GeoTIFF от коригираните канали
                output_path = _build_composite(corrected_bands, input_path, output_dir)
                logger.success(f"ACOLITE корекция завършена. Резултат: {output_path}")
                return output_path
            else:
                logger.warning("ACOLITE не върна коригирани канали. Преминаване към базова обработка.")
                
        except Exception as e:
            logger.warning(f"ACOLITE корекцията е неуспешна: {e}. Преминаване към базова обработка.")
    
    elif not acolite_available():
        logger.info("ACOLITE не е наличен. Използва се базова обработка.")
    elif not l1c_path:
        logger.info("L1C данни не са налични. Използва се базова обработка на L2A.")
    
    # ── Стъпка 2: Базова обработка (fallback) ──
    return _basic_preprocess(input_path)


def _build_composite(corrected_bands: dict, reference_path: str, output_dir: str) -> str:
    """
    Създава композитен GeoTIFF от ACOLITE-коригирани спектрални канали.
    
    Обединява отделните rhow_* канали (B2, B3, B4, B8) в един
    многоканален GeoTIFF, съвместим с downstream пайплайна.
    
    Args:
        corrected_bands: Речник {band_name: path} от ACOLITE.
        reference_path: Път до оригиналния файл за наименуване.
        output_dir: Директория за запис.
        
    Returns:
        str: Път до композитния GeoTIFF.
    """
    # Реда на каналите за композита
    band_order = ['b2', 'b3', 'b4', 'b8']
    available_bands = [b for b in band_order if b in corrected_bands]
    
    if not available_bands:
        raise ValueError("Няма налични ACOLITE канали за композит.")
    
    # Четене на референтния канал за метаданни (размери, проекция)
    first_band_path = corrected_bands[available_bands[0]]
    with rasterio.open(first_band_path) as ref:
        height, width = ref.height, ref.width
        profile = ref.profile.copy()
    
    # Обновяване на профила за многоканален файл
    profile.update(count=len(available_bands), dtype='float32')
    
    output_path = reference_path.replace(".tif", "_acolite_processed.tif")
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        for i, band_name in enumerate(available_bands, start=1):
            with rasterio.open(corrected_bands[band_name]) as src:
                data = src.read(1)
                dst.write(data.astype(np.float32), i)
                dst.set_band_description(i, f"ACOLITE rhow {band_name}")
    
    logger.info(f"Композит създаден: {len(available_bands)} канала → {output_path}")
    return output_path


def _basic_preprocess(input_path: str) -> str:
    """
    Базова предварителна обработка (passthrough) за случаите, когато
    ACOLITE не е наличен. Копира входния файл, запазвайки метаданните.
    
    Args:
        input_path: Път до входния GeoTIFF.
        
    Returns:
        str: Път до обработения файл.
    """
    logger.info("Изпълнение на базова предварителна обработка (без ACOLITE)...")
    
    output_path = input_path.replace(".tif", "_processed.tif")
    
    with rasterio.open(input_path) as src:
        profile = src.profile
        data = src.read()
        
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(data)
            for i in range(1, src.count + 1):
                if src.descriptions[i-1]:
                    dst.set_band_description(i, src.descriptions[i-1])
                    
    logger.success(f"Базова обработка завършена. Записано в: {output_path}")
    return output_path
