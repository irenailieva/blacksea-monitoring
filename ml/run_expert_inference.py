import os
from pathlib import Path
from model import load_model
from image_processor import process_scene

# ==============================================================================
# СКРИПТ ЗА ЕКСПЕРТЕН АНАЛИЗ НА СЦЕНА (EXPERT INFERENCE)
# Този скрипт се използва за ръчно стартиране на процеса по обработка
# на конкретна сателитна снимка. Прочита спектралните канали, 
# зарежда модела и генерира TIF карта с класификация.
# ==============================================================================

def run_inference():
    """
    Основна функция за изпълнение на анализа.
    """
    # Дефиниране на пътищата
    # Забележка: Скриптът предполага изпълнение в Docker контейнер, където
    # локалните папки са монтирани в /app/...
    base_dir = Path("/app/data/inference")
    output_path = base_dir / "output_classification.tif" # Файлът, в който ще запишем резултата
    artifacts_dir = Path("/app/artifacts")               # Директория с обучените модели

    # Дефиниране на пътищата до отделните Sentinel-2 канали (от определена дата)
    band_paths = {
        'b2': str(base_dir / "T35TNH_20250910T085721_B02_10m.jp2"),   # Синьо
        'b3': str(base_dir / "T35TNH_20250910T085721_B03_10m.jp2"),   # Зелено
        'b4': str(base_dir / "T35TNH_20250910T085721_B04_10m.jp2"),   # Червено
        'b8': str(base_dir / "T35TNH_20250910T085721_B08_10m.jp2"),   # Близко инфрачервено (NIR)
        'scl': str(base_dir / "T35TNH_20250910T085721_SCL_20m.jp2")  # Класификация на сцената (Облаци/Суша)
    }

    # 1. Проверка дали всички необходими файлове съществуват
    for b, p in band_paths.items():
        if not os.path.exists(p):
            print(f"Грешка: Необходимият файл не е намерен: {p}")
            return

    # 2. Зареждане на ансамбъла от ML модели
    print("Зареждане на модела...")
    try:
        model = load_model(artifacts_dir)
    except Exception as e:
        print(f"Грешка при зареждане на модела: {e}")
        return

    # 3. Стартиране на процеса по обработка
    print("Стартиране на анализа (inference)...")
    try:
        # Извикваме основната функция от image_processor, която ще прочете
        # изображението на блокове, ще го маскира и класифицира.
        process_scene(band_paths, str(output_path), model)
    except Exception as e:
        print(f"Грешка при обработката на сцената: {e}")
        return
    
    print(f"Готово.")

if __name__ == "__main__":
    run_inference()
