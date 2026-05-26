import os
from pathlib import Path
from model import load_model
from image_processor import process_scene

# ==============================================================================
# СКРИПТ ЗА АНАЛИЗ НА ЕЗЕРОТО ВАЯ (LAKE VAYA INFERENCE)
# Подобно на run_expert_inference.py, но специализиран за обработка на
# конкретна сцена от езерото Вая. Често се ползва за валидация на модела
# върху специфичен регион от интерес (ROI).
# ==============================================================================

def run_inference():
    """
    Основна функция за изпълнение на анализа за езерото Вая.
    """
    # Дефиниране на пътищата
    # Както и в другия скрипт, очакваме да се изпълнява в Docker контейнер
    base_dir = Path("/app/data/inference/lake-vaya")
    output_path = base_dir / "output_classification.tif" # Път до изходния резултат
    artifacts_dir = Path("/app/artifacts")               # Път до обучените модели

    # Дефиниране на пътища до каналите от сцената на езерото Вая (дата: 2023-06-06)
    band_paths = {
        'b2': str(base_dir / "T35TNH_20230606T085559_B02_10m.jp2"),
        'b3': str(base_dir / "T35TNH_20230606T085559_B03_10m.jp2"),
        'b4': str(base_dir / "T35TNH_20230606T085559_B04_10m.jp2"),
        'b8': str(base_dir / "T35TNH_20230606T085559_B08_10m.jp2"),
        'scl': str(base_dir / "T35TNH_20230606T085559_SCL_20m.jp2")
    }

    # 1. Проверка за съществуването на файловете
    print(f"Проверка на файловете в {base_dir}...")
    for b, p in band_paths.items():
        if not os.path.exists(p):
            print(f"Грешка: Липсва файл: {p}")
            return
    print("Всички файлове са намерени.")

    # 2. Зареждане на машинното обучение
    print("Зареждане на ML моделите...")
    try:
        model = load_model(artifacts_dir)
    except Exception as e:
        print(f"Грешка при зареждане на моделите: {e}")
        return

    # 3. Изпълнение на анализа и класификацията
    print(f"Стартиране на класификацията за езерото Вая...")
    print(f"Резултатът ще бъде запазен в: {output_path}")
    
    try:
        # Изпращаме пътищата на функцията process_scene, която върши същинската работа
        process_scene(band_paths, str(output_path), model)
    except Exception as e:
        print(f"Възникна грешка по време на обработката: {e}")
        return

if __name__ == "__main__":
    run_inference()
