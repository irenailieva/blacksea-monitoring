import os
import glob
import re
import pandas as pd
import rasterio
import numpy as np
from pathlib import Path
from loguru import logger

# Функция за извличане на дата от името на файла
def extract_date_from_filename(filename: str) -> str:
    """
    Extracts date from filename. 
    Expects format like sentinel2_{id}.tif or mock_sentinel2.tif
    For mock data, returns a default date.
    For real data (if filename contains date), extracts it.
    Otherwise returns a placeholder.
    """
    # Търсене на дата във формат YYYY-MM-DD или YYYYMMDD чрез регулярен израз
    match = re.search(r"(\d{4}[-_]\d{2}[-_]\d{2})", filename)
    if match:
        return match.group(1)
    
    # Връщане на стойност по подразбиране (placeholder) за mock данни или неразпознат формат
    return "2024-01-01"

# Функция за експортиране на данни от GeoTIFF към CSV формат
def export_to_csv(input_dir: str, output_csv: str):
    """
    Reads all .tif files in input_dir, flattens them, and appends to a CSV.
    """
    logger.info(f"Exporting data from {input_dir} to {output_csv}...")
    
    # Намиране на всички .tif файлове в посочената входна директория
    tif_files = glob.glob(os.path.join(input_dir, "*.tif"))
    if not tif_files:
        logger.warning(f"No .tif files found in {input_dir}")
        return

    all_data = []

    # Итерация през всеки намерен .tif файл
    for tif_path in tif_files:
        filename = os.path.basename(tif_path)
        # Пропускане на междинни обработени файлове, ако е необходимо.
        # В момента четем всички файлове, които приличат на изображение.
        if "processed" in filename: 
            # Ако имаме както сурови, така и обработени данни, избягваме дублирането.
            # Оставя се празен блок (pass) за бъдеща логика за филтриране.
            pass

        # Извличане на дата от текущия файл
        date_str = extract_date_from_filename(filename)
        
        # Отваряне на растерния файл чрез rasterio
        with rasterio.open(tif_path) as src:
            # Очакваме изображението да има 4 канала: Blue, Green, Red, NIR.
            # Пропускаме файла, ако каналите са по-малко.
            if src.count < 4:
                logger.warning(f"Skipping {filename}: expected at least 4 bands, got {src.count}")
                continue

            # Прочитане на всички пиксели от всички канали
            # Форматът на данните е (брой_канали, височина, ширина)
            data = src.read()
            
            bands, height, width = data.shape
            
            # Създаване на координатна мрежа (meshgrid) за X и Y координатите
            # X е колоната (ширината), Y е редът (височината)
            cols, rows = np.meshgrid(np.arange(width), np.arange(height))
            
            # Сплескване (flatten) на двумерните масиви в едномерни.
            # Целта е всеки пиксел да стане отделен ред в DataFrame.
            
            rows_flat = rows.flatten()
            cols_flat = cols.flatten()
            
            # Извличане на стойностите за съответните спектрални канали
            b1 = data[0].flatten() # Синьо (Blue)
            b2 = data[1].flatten() # Зелено (Green)
            b3 = data[2].flatten() # Червено (Red)
            b4 = data[3].flatten() # Близък инфрачервен (NIR)
            
            # Създаване на pandas DataFrame, съдържащ данните за всеки пиксел от изображението
            df_img = pd.DataFrame({
                'date': date_str,
                'x': cols_flat,
                'y': rows_flat,
                'blue': b1,
                'green': b2,
                'red': b3,
                'nir': b4,
                'target': 0.0 # Първоначална стойност (placeholder) за целевия клас
            })
            
            # Добавяне на данните към общия списък
            all_data.append(df_img)
            logger.info(f"Processed {filename}: {len(df_img)} pixels")

    # Проверка дали са извлечени някакви данни
    if not all_data:
        logger.warning("No data extracted.")
        return

    # Обединяване на всички DataFrame-и в един общ
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Гарантиране, че изходната директория съществува
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    # Експортиране на данните в CSV файл, без индексна колона
    final_df.to_csv(output_csv, index=False)
    logger.success(f"Successfully exported {len(final_df)} rows to {output_csv}")

# Изпълнение на скрипта при директно стартиране
if __name__ == "__main__":
    # Тестово стартиране.
    # Предполага се, че скриптът се изпълнява от основната директория на проекта.
    IN_DIR = "etl/out" 
    OUT_CSV = "ml/data/train.csv"
    
    # Проверка дали скриптът се изпълнява вътре в Docker контейнер (директория /app)
    if os.path.exists("/app/out"):
        IN_DIR = "/app/out"
        OUT_CSV = "/app/ml/data/train.csv"
        
    export_to_csv(IN_DIR, OUT_CSV)
