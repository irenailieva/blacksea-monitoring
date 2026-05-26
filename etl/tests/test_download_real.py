import os
import sys
from loguru import logger

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from flows.downloader import download_data

# Тестова функция за реално изтегляне на сателитни данни
def test_real_download():
    # Конфигурация за теста: дефиниране на зона на интерес (AOI)
    aoi = {
        "bbox": [27.85, 43.20, 27.95, 43.25]  # Ограничаваща рамка за Варненския залив
    }
    
    # Дефиниране на времеви обхват за търсене на сателитни сцени
    time_range = {
        "start_date": "2024-06-01",
        "end_date": "2024-06-30"
    }
    
    # Директория, в която ще бъдат запазени изтеглените файлове по време на теста
    output_dir = "test_out"
    
    logger.info("Starting real download test...")
    try:
        # Извикване на функцията за изтегляне в режим 'real'
        result_path = download_data(aoi, time_range, output_dir, mode="real")
        
        # Проверка дали файлът е успешно създаден (има врънат път)
        if result_path and os.path.exists(result_path.get("composite", "")):
            composite_file = result_path["composite"]
            logger.success(f"Test passed! File downloaded to: {composite_file}")
            
            # Базова проверка дали файлът не е празен
            if os.path.getsize(composite_file) > 0:
                logger.info("File size is greater than 0.")
            else:
                logger.error("File is empty.")
        else:
            logger.error("Test failed! File was not created.")
            
    except Exception as e:
        # Прихващане и логване на всякакви грешки по време на теста
        logger.exception(f"Test failed with exception: {e}")

# Изпълнение на теста при директно стартиране на скрипта
if __name__ == "__main__":
    test_real_download()
