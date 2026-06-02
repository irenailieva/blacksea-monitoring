import os
import sys
import glob
import shutil
import tempfile
import numpy as np
from loguru import logger

# ==============================================================================
# ACOLITE АТМОСФЕРНА КОРЕКЦИЯ (ACOLITE_CORRECTOR.PY)
# Този модул интегрира процесора ACOLITE за атмосферна корекция на сателитни
# изображения от Sentinel-2. Използва алгоритъма Dark Spectrum Fitting (DSF),
# оптимизиран за акватични приложения, който е значително по-точен от
# стандартната ESA Sen2Cor корекция за крайбрежни и вътрешни води.
# ==============================================================================

# Опит за импортиране на ACOLITE (инсталира се като git clone в /opt/acolite)
_acolite_available = False
try:
    import acolite as ac
    _acolite_available = True
    logger.info("ACOLITE е наличен и готов за употреба.")
except ImportError:
    logger.warning(
        "ACOLITE не е инсталиран. Атмосферната корекция ще бъде пропусната. "
        "Инсталирайте с: git clone https://github.com/acolite/acolite.git /opt/acolite"
    )


def is_available() -> bool:
    """Проверява дали ACOLITE е наличен в системата."""
    return _acolite_available


def generate_settings(input_path: str, output_dir: str, aoi_bbox: list = None) -> dict:
    """
    Генерира конфигурационен речник (settings) за ACOLITE процесора.
    
    Настройките са оптимизирани за оптично сложните води на Черно море,
    където стандартните атмосферни корекции (Sen2Cor) не са достатъчно
    прецизни за детекция на подводна растителност.
    
    Args:
        input_path: Път до L1C .SAFE директория или GeoTIFF файл.
        output_dir: Директория за запис на коригираните данни.
        aoi_bbox: Ограничителна рамка [minLon, minLat, maxLon, maxLat].
        
    Returns:
        dict: Конфигурация за ACOLITE, готова за подаване на acolite_run().
    """
    settings = {
        # Входни и изходни пътища
        'inputfile': input_path,
        'output': output_dir,
        
        # Алгоритъм за атмосферна корекция: Dark Spectrum Fitting
        # DSF идентифицира "тъмни" пиксели (с нулева повърхностна отражателност)
        # и моделира атмосферната пътна светлина за елиминиране на аерозоли
        'atmospheric_correction': 'dark_spectrum',
        'dsf_aot_estimate': 'fixed',
        
        # Изходни L2W (Level 2 Water) продукти
        # rhow_* — водно-напускаща отражателност за всички спектрални канали
        'l2w_parameters': ['rhow_*'],
        
        # Корекция на слънчеви отблясъци (Sun Glint Correction)
        # Критично за Черно море, където водната повърхност действа като огледало
        'glint_correction': True,
        
        # Разделителна способност за Sentinel-2
        # 10m е стандартната резолюция за видимите канали (B2, B3, B4) и NIR (B8)
        's2_target_res': 10,
        
        # Формат на изхода
        'output_geotiff': True,
        'merge_tiles': True,
    }
    
    # Пространствено ограничаване (subsetting) по AOI
    # ACOLITE очаква формат [S, W, N, E] (Юг, Запад, Север, Изток)
    if aoi_bbox and len(aoi_bbox) == 4:
        min_lon, min_lat, max_lon, max_lat = aoi_bbox
        settings['limit'] = [min_lat, min_lon, max_lat, max_lon]
    else:
        # Граници по подразбиране за българското черноморско крайбрежие
        settings['limit'] = [41.0, 27.0, 44.0, 32.0]
    
    return settings


def _find_output_files(output_dir: str, pattern: str = "*.tif") -> list:
    """
    Намира всички генерирани файлове от ACOLITE в изходната директория.
    
    ACOLITE създава файлове с имена като:
    - *_rhow_443.tif (синьо)
    - *_rhow_560.tif (зелено)
    - *_rhow_665.tif (червено)
    - *_rhow_833.tif (NIR)
    """
    return sorted(glob.glob(os.path.join(output_dir, pattern)))


def _find_netcdf_outputs(output_dir: str) -> list:
    """Намира NetCDF изходни файлове от ACOLITE (L2R/L2W)."""
    nc_files = glob.glob(os.path.join(output_dir, "*.nc"))
    return sorted(nc_files)


def _convert_netcdf_to_geotiff(nc_path: str, output_dir: str, bands_of_interest: list = None) -> dict:
    """
    Конвертира ACOLITE NetCDF изход към GeoTIFF файлове.
    
    ACOLITE по подразбиране произвежда NetCDF файлове с множество променливи.
    За интеграция с останалата част от ETL пайплайна (Rasterio-базиран),
    е необходимо конвертиране към GeoTIFF.
    
    Args:
        nc_path: Път до NetCDF файла от ACOLITE.
        output_dir: Директория за запис на GeoTIFF файловете.
        bands_of_interest: Списък от имена на канали за извличане.
        
    Returns:
        dict: Пътища към конвертираните GeoTIFF файлове по тип канал.
    """
    import rasterio
    from rasterio.transform import from_bounds
    
    try:
        import netCDF4 as nc4
    except ImportError:
        logger.error("netCDF4 не е инсталиран. Необходим за конвертиране на ACOLITE изхода.")
        raise
    
    # Спектрални канали на Sentinel-2 и съответните ACOLITE имена
    # Тези дължини на вълната съответстват на B2, B3, B4, B8
    if bands_of_interest is None:
        bands_of_interest = {
            'rhow_492': 'b2',    # Синьо (Blue) — B2 (492nm)
            'rhow_560': 'b3',    # Зелено (Green) — B3 (560nm)
            'rhow_665': 'b4',    # Червено (Red) — B4 (665nm)
            'rhow_833': 'b8',    # Близък инфрачервен (NIR) — B8 (833nm)
        }
    
    result_paths = {}
    
    # Отваряне на NetCDF файла
    dataset = nc4.Dataset(nc_path, 'r')
    
    try:
        # Извличане на координатите за георефериране
        if 'lat' in dataset.variables and 'lon' in dataset.variables:
            lat = dataset.variables['lat'][:]
            lon = dataset.variables['lon'][:]
            
            # Изчисляване на границите на изображението
            min_lat, max_lat = float(np.nanmin(lat)), float(np.nanmax(lat))
            min_lon, max_lon = float(np.nanmin(lon)), float(np.nanmax(lon))
        else:
            logger.warning("Координатни променливи липсват в NetCDF файла.")
            dataset.close()
            return result_paths
        
        # Итерация през желаните спектрални канали
        for nc_var, ml_name in bands_of_interest.items():
            if nc_var not in dataset.variables:
                # Опит за намиране на алтернативни имена (ACOLITE версиите варират)
                alt_names = [v for v in dataset.variables if nc_var.split('_')[1] in v]
                if alt_names:
                    nc_var = alt_names[0]
                else:
                    logger.warning(f"Каналът '{nc_var}' не е намерен в ACOLITE изхода. Пропускане.")
                    continue
            
            # Извличане на данните за канала
            data = dataset.variables[nc_var][:]
            if data.ndim > 2:
                data = data[0]  # Премахване на допълнителни измерения
            
            # Определяне на размерите
            height, width = data.shape
            
            # Създаване на GeoTIFF с правилно георефериране
            transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)
            
            output_path = os.path.join(output_dir, f"acolite_{ml_name}.tif")
            
            profile = {
                'driver': 'GTiff',
                'dtype': 'float32',
                'width': width,
                'height': height,
                'count': 1,
                'crs': 'EPSG:4326',
                'transform': transform,
                'nodata': np.nan,
            }
            
            with rasterio.open(output_path, 'w', **profile) as dst:
                # Записване на коригираните данни за водно-напускаща отражателност
                dst.write(np.array(data, dtype=np.float32), 1)
                dst.set_band_description(1, f"ACOLITE {nc_var}")
            
            result_paths[ml_name] = output_path
            logger.info(f"  Конвертиран: {nc_var} → {output_path}")
        
    finally:
        dataset.close()
    
    return result_paths


def apply_acolite_correction(input_path: str, output_dir: str, aoi_bbox: list = None) -> dict:
    """
    Прилага ACOLITE атмосферна корекция (Dark Spectrum Fitting) върху
    сателитно изображение от Sentinel-2.
    
    Основната функция на модула. Управлява целия процес:
    1. Генериране на ACOLITE конфигурация, оптимизирана за Черно море
    2. Изпълнение на DSF атмосферната корекция
    3. Конвертиране на изхода (NetCDF → GeoTIFF)
    4. Връщане на пътищата към коригираните спектрални канали
    
    Args:
        input_path: Път до L1C .SAFE директория или входен GeoTIFF файл.
        output_dir: Директория за запис на коригираните данни.
        aoi_bbox: Ограничителна рамка [minLon, minLat, maxLon, maxLat].
        
    Returns:
        dict: Речник с пътища към коригираните канали:
              {'b2': '...tif', 'b3': '...tif', 'b4': '...tif', 'b8': '...tif'}
              
    Raises:
        RuntimeError: Ако ACOLITE не е наличен или корекцията е неуспешна.
    """
    if not _acolite_available:
        raise RuntimeError(
            "ACOLITE не е инсталиран. Моля, клонирайте хранилището: "
            "git clone https://github.com/acolite/acolite.git /opt/acolite"
        )
    
    logger.info(f"Стартиране на ACOLITE атмосферна корекция за: {input_path}")
    
    # Създаване на изходна директория за ACOLITE резултатите
    acolite_out = os.path.join(output_dir, "acolite_output")
    os.makedirs(acolite_out, exist_ok=True)
    
    # Генериране на конфигурация
    settings = generate_settings(input_path, acolite_out, aoi_bbox)
    
    logger.info(f"ACOLITE настройки: limit={settings.get('limit')}, "
                f"dsf_aot_estimate={settings.get('dsf_aot_estimate')}")
    
    try:
        # Изпълнение на ACOLITE процесора
        # acolite_run() е главната входна точка на ACOLITE Python API
        ac.acolite.acolite_run(settings=settings)
        logger.success("ACOLITE корекцията приключи успешно.")
        
    except Exception as e:
        logger.error(f"ACOLITE корекцията е неуспешна: {e}")
        raise RuntimeError(f"ACOLITE грешка: {e}") from e
    
    # Проверка за генерирани GeoTIFF файлове (ако output_geotiff=True е работило)
    geotiff_outputs = _find_output_files(acolite_out, "*.tif")
    
    if geotiff_outputs:
        logger.info(f"Намерени {len(geotiff_outputs)} GeoTIFF файла от ACOLITE.")
        # Преобразуване на ACOLITE файлове към стандартните ML имена
        result = _map_acolite_tifs(geotiff_outputs, output_dir)
    else:
        # Ако GeoTIFF не са генерирани, търсим NetCDF файлове
        nc_files = _find_netcdf_outputs(acolite_out)
        if not nc_files:
            raise RuntimeError(
                f"ACOLITE не е генерирал изходни файлове в {acolite_out}. "
                "Проверете входните данни и настройките."
            )
        
        logger.info(f"Конвертиране на {len(nc_files)} NetCDF файла към GeoTIFF...")
        
        # Използваме L2W файла (водно-напускаща отражателност), ако е наличен
        l2w_files = [f for f in nc_files if 'L2W' in f]
        target_nc = l2w_files[0] if l2w_files else nc_files[-1]
        
        result = _convert_netcdf_to_geotiff(target_nc, output_dir)
    
    if not result:
        raise RuntimeError("ACOLITE не е произвел валидни спектрални канали.")
    
    logger.success(f"ACOLITE коригирани канали: {list(result.keys())}")
    return result


def _map_acolite_tifs(tif_files: list, output_dir: str) -> dict:
    """
    Преобразува ACOLITE GeoTIFF файлове към стандартните имена на каналите
    за ML пайплайна (b2, b3, b4, b8).
    
    ACOLITE наименува файловете си по дължина на вълната (напр. *_rhow_492.tif).
    Тази функция ги мапва към Sentinel-2 Band номерата.
    """
    import rasterio
    
    # Mapping на ACOLITE вълнови дължини → Sentinel-2 канали
    wavelength_map = {
        '443': 'b1',   # Coastal aerosol
        '492': 'b2',   # Blue
        '560': 'b3',   # Green
        '665': 'b4',   # Red
        '704': 'b5',   # Vegetation Red Edge 1
        '740': 'b6',   # Vegetation Red Edge 2
        '783': 'b7',   # Vegetation Red Edge 3
        '833': 'b8',   # NIR
        '865': 'b8a',  # Narrow NIR
    }
    
    # Канали, необходими за ML модела
    needed = {'b2', 'b3', 'b4', 'b8'}
    result = {}
    
    for tif in tif_files:
        basename = os.path.basename(tif).lower()
        for wavelength, band_name in wavelength_map.items():
            if wavelength in basename and band_name in needed:
                # Копиране на файла с нормализирано име
                dest = os.path.join(output_dir, f"acolite_{band_name}.tif")
                shutil.copy2(tif, dest)
                result[band_name] = dest
                logger.info(f"  Мапнат: {basename} → {band_name} ({dest})")
                break
    
    return result
