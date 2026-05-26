import os
import numpy as np
import rasterio
from rasterio.transform import from_origin
from loguru import logger
import pystac_client
import odc.stac
import rioxarray
import threading
import time

# Клас за симулиране на прогреса на дадена задача (напр. изтегляне на данни).
# Използва се за обратна връзка в потребителския интерфейс (показване на лента за прогрес).
class ProgressSimulator:
    def __init__(self, callback, start, end, duration=30):
        self.callback = callback # Функция за извикване при обновяване на прогреса
        self.start = start       # Начална стойност на прогреса
        self.end = end           # Крайна стойност на прогреса
        self.duration = duration # Очаквана продължителност в секунди
        self.stop_requested = False
        self.thread = threading.Thread(target=self.run) # Нишка, в която се изпълнява симулацията
    # Стартиране на симулацията в отделна нишка
    def start_sim(self):
        self.thread.start()
    # Основен цикъл на симулацията - плавно увеличава прогреса от start до end
    def run(self):
        steps = 30
        step_time = self.duration / steps
        for i in range(steps):
            if self.stop_requested:
                break
            if self.callback:
                self.callback(self.start + (self.end - self.start) * (i / steps))
            time.sleep(step_time)
    # Принудително спиране на симулацията, например ако реалната задача приключи по-рано
    def stop(self):
        self.stop_requested = True
        if self.thread.is_alive():
            self.thread.join()

# Основна функция за изтегляне на сателитни данни Sentinel-2
def download_data(aoi: dict, time_range: dict, output_dir: str, mode: str = "mock", cloud_max: int = 20, progress_callback=None) -> dict:
    """
    Downloads Sentinel-2 data or generates a mock GeoTIFF.
    
    Args:
        aoi (dict): Area of Interest configuration.
        time_range (dict): Time range configuration.
        output_dir (str): Directory to save the downloaded file.
        mode (str): 'mock' or 'real'.
        progress_callback (callable): Optional callback for progress updates.
        
    Returns:
        dict: Dictionary containing 'composite' path and 'ml_bands' dict.
    """
    # Създаване на изходната директория, ако тя все още не съществува
    os.makedirs(output_dir, exist_ok=True)
    
    if mode == "mock":
        # Мокъп режимът (за симулиране на данни) е изключен, връща се грешка
        raise NotImplementedError("Mock mode has been disabled. Please use 'real' mode.")
        
    elif mode == "real":
        # Логване на началото на процеса за търсене на данни
        logger.info("Searching for Sentinel-2 data via STAC...")
        
        # STAC API URL адрес на Earth Search за достъп до AWS колекции
        STAC_URL = "https://earth-search.aws.element84.com/v1"
        
        # Извличане на ограничителната рамка (Bounding Box) от конфигурацията на зоната на интерес (AOI)
        bbox = aoi.get("bbox")
        if not bbox:
            raise ValueError("AOI must contain a 'bbox' [min_lon, min_lat, max_lon, max_lat]")
            
        # Формиране на заявка за времеви обхват във формат ISO8601 (start/end)
        start_date = time_range.get("start_date")
        end_date = time_range.get("end_date")
        datetime_query = f"{start_date}/{end_date}"
        
        try:
            # Отваряне на връзка към STAC каталога
            client = pystac_client.Client.open(STAC_URL)
            
            # Извършване на търсене (search) за колекцията Sentinel-2 Level-2A (коригирани атмосферни влияния)
            search = client.search(
                collections=["sentinel-2-l2a"],
                bbox=bbox,
                datetime=datetime_query,
                max_items=10, # Ограничаваме до 10 резултата
                query={"eo:cloud_cover": {"lt": cloud_max}} # Филтър: облачно покритие по-малко от cloud_max
            )
            
            # Извличане на намерените елементи
            items = list(search.item_collection())
            
            # Проверка дали са намерени подходящи сцени
            if not items:
                logger.warning("No Sentinel-2 scenes found for this AOI and date range.")
                raise FileNotFoundError("No Satellite scenes found. Check your search parameters.")
                
            logger.info(f"Found {len(items)} scenes. Processing the most recent one...")
            item = items[0]  # Взимане на най-скорошната сцена (STAC по подразбиране връща най-новите първо)
            
            # Симулиране на прогрес за изтеглянето на данните
            if progress_callback:
                progress_callback(10)
                sim = ProgressSimulator(progress_callback, 10, 90, duration=45)
                sim.start_sim()
            
            # Зареждане на нужните спектрални канали (Bands) в една заявка за ефективност.
            # Използваме само първия елемент [item], вместо целия списък [items].
            ds = odc.stac.load(
                [item],
                bands=["blue", "green", "red", "nir", "scl"],
                bbox=bbox,
                crs="EPSG:4326",
                resolution=0.0001
            )
            
            # Спиране на симулатора, тъй като данните са изтеглени и заредени
            if progress_callback:
                sim.stop()
                progress_callback(90)
            
            # Премахване на измерението "time", ако съществува, тъй като работим само с една сцена
            if "time" in ds.dims:
                ds = ds.isel(time=0)
                
            # Дефиниране на файловото име и пътя за запазване на композитното изображение
            composite_filename = f"sentinel2_{item.id}.tif"
            composite_filepath = os.path.join(output_dir, composite_filename)
            
            # Създаване и запазване на композитно изображение (с 4 канала) за визуализация в интерфейса (Dashboard)
            ds_composite = ds[["blue", "green", "red", "nir"]]
            da_composite = ds_composite.to_array(dim="band")
            da_composite.rio.to_raster(composite_filepath)
            
            # Обновяване на прогреса
            if progress_callback:
                progress_callback(95)
            
            # --- Запазване на отделни спектрални канали за нуждите на машинното обучение (ML) ---
            ml_band_paths = {}
            band_map = {
                "blue": "b2", "green": "b3", "red": "b4", "nir": "b8", "scl": "scl"
            }

            # Итерация през всеки канал, експортиране в GeoTIFF и записване на пътя към файла
            for i, (stac_name, ml_name) in enumerate(band_map.items()):
                band_filename = f"sentinel2_{item.id}_{ml_name}.tif"
                band_filepath = os.path.join(output_dir, band_filename)
                ds[stac_name].rio.to_raster(band_filepath)
                ml_band_paths[ml_name] = band_filepath
                
                # Постепенно увеличаване на лентата за прогрес
                if progress_callback:
                    progress_callback(95 + i + 1)
            
            # Логване на успешния резултат и връщане на метаданните
            logger.success(f"Downloaded real data for item {item.id} to {composite_filepath}")
            return {
                "composite": composite_filepath,
                "ml_bands": ml_band_paths,
                "stac_item_id": item.id,
                "all_stac_ids": [i.id for i in items],
                "cloud_cover": item.properties.get("eo:cloud_cover", 0.0),
            }
            
        except Exception as e:
            # Прихващане и логване на грешки при изтеглянето на данните
            logger.error(f"Failed to download real data: {e}")
            raise
