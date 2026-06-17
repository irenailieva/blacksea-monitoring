import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling
import numpy as np
import pandas as pd
from pathlib import Path
import time

# ==============================================================================
# СКРИПТ ЗА АВТОМАТИЧНО ИЗВЛИЧАНЕ НА ОБУЧАВАЩИ ДАННИ (FORCE-LEARNING)
# Този скрипт чете сателитни снимки от езерото Вая, трансформира координатите,
# изчислява спектрални индекси (NDVI, NDWI) и на тяхна база автоматично
# класифицира пиксели (вода, суша, растителност), които записва в CSV файл.
# ==============================================================================

# -- КОНФИГУРАЦИЯ НА ПЪТИЩАТА --
# Директория с данните от Sentinel-2 за езерото Вая
BASE_DIR = Path(r"C:\Users\irena\Downloads\vaya_lake_tiffs")
OUTPUT_CSV = Path(__file__).parent / "dataset.csv"

# Пътища до отделните спектрални канали (Bands)
B2_PATH = BASE_DIR / "T35TNH_20230606T085559_B02_10m.jp2"  # Син канал
B3_PATH = BASE_DIR / "T35TNH_20230606T085559_B03_10m.jp2"  # Зелен канал
B4_PATH = BASE_DIR / "T35TNH_20230606T085559_B04_10m.jp2"  # Червен канал
B8_PATH = BASE_DIR / "T35TNH_20230606T085559_B08_10m.jp2"  # Близък инфрачервен канал (NIR)
SCL_PATH = BASE_DIR / "T35TNH_20230606T085559_SCL_20m.jp2" # Слой за класификация на сцената (суша, вода, облаци)

# Регион на интерес (ROI): Ограничаваща кутия (Bounding Box) около езерото Вая в координати WGS84 (Географска дължина/ширина)
MEAN_ROI_WGS84 = (27.3319, 42.4727, 27.4932, 42.5235)

def extract_data():
    """
    Основна функция за извличане на данни, базирана на предефинирани спектрални правила (Force-Learning).
    """
    start_time = time.time()
    print(f"[{time.time()-start_time:.1f}s] --- Стартиране извличането на данни за езерото Вая (Force-Learning) ---")
    
    # 1. Определяне на прозореца за четене (Window)
    # Понеже сателитната сцена е много голяма, ние ще четем само пикселите, които попадат в
    # нашата ограничаваща кутия (ROI).
    window = None
    
    with rasterio.open(B2_PATH) as src:
        print(f"[{time.time()-start_time:.1f}s] Изходна координатна система (CRS): {src.crs}")
        # Трансформиране на WGS84 координатите (Lat/Lon) в координатната система на сателитната снимка (UTM)
        left, bottom, right, top = transform_bounds("EPSG:4326", src.crs, *MEAN_ROI_WGS84)
        # Създаване на обект 'window' на базата на трансформираните координати
        window = from_bounds(left, bottom, right, top, transform=src.transform)
        print(f"[{time.time()-start_time:.1f}s] Прозорец за четене: {window}")

    # 2. Четене на спектралните канали (само в рамките на прозореца)
    print(f"[{time.time()-start_time:.1f}s] Четене на каналите (вкл. SCL)...")
    with rasterio.open(B2_PATH) as src_b2, \
         rasterio.open(B3_PATH) as src_b3, \
         rasterio.open(B4_PATH) as src_b4, \
         rasterio.open(B8_PATH) as src_b8, \
         rasterio.open(SCL_PATH) as src_scl:
         
        # Четене на каналите с 10m разделителна способност
        b2 = src_b2.read(1, window=window).astype(float)
        print(f"[{time.time()-start_time:.1f}s] Канал B2 (Син) прочетен. Размери: {b2.shape}")
        
        b3 = src_b3.read(1, window=window).astype(float)
        b4 = src_b4.read(1, window=window).astype(float)
        b8 = src_b8.read(1, window=window).astype(float)
        
        # SCL слоят е с 20m резолюция, затова трябва да се преоразмери (Upscaling),
        # за да съвпадне с размерите на 10-метровите канали.
        scl_window = from_bounds(left, bottom, right, top, transform=src_scl.transform)
        print(f"[{time.time()-start_time:.1f}s] Четене на SCL. Прозорец: {scl_window}")
        
        scl_raw = src_scl.read(
            1, 
            window=scl_window,
            out_shape=(b2.shape[0], b2.shape[1]), # Принудително изравняване на размерите
            resampling=Resampling.nearest # Използване на 'най-близък съсед' за категорийни данни
        )
        print(f"[{time.time()-start_time:.1f}s] SCL прочетен. Размери: {scl_raw.shape}")

    import utils
    # Extract features using centralized utility (which properly corrects BOA offset)
    # We must flatten the 2D arrays because prepare_features uses np.column_stack which expects 1D arrays.
    features = utils.prepare_features(b2.flatten(), b3.flatten(), b4.flatten(), b8.flatten())
    b2_calib = features[:, 0].reshape(b2.shape)
    b3_calib = features[:, 1].reshape(b3.shape)
    b4_calib = features[:, 2].reshape(b4.shape)
    b8_calib = features[:, 3].reshape(b8.shape)
    ndvi = features[:, 4].reshape(b2.shape)
    ndwi = features[:, 5].reshape(b2.shape)
    
    # 4. Прилагане на правилата за автоматично маркиране (Force-Learning)
    print(" Прилагане на правилата за създаване на етикети (Labels)...")
    # Създаване на масив, пълен със стойности -1 (некласифицирани пиксели)
    labels = np.full(ndvi.shape, -1, dtype=int)
    
    # ЦЕЛ: Клас 2 (Дълбока вода) -> Обикновено NDVI е много ниско за вода.
    # Маркираме пикселите с NDVI <= 0.0 като вода (като базов слой).
    labels[ndvi <= 0.0] = 2
    
    # ЦЕЛ: Клас 0 (Суша/Абиотични) -> NDVI < 0.1 И SCL == 5 (Нерастителни почви)
    # Това помага да избегнем класифицирането на бреговете или пясъка като нещо друго.
    labels[(ndvi < 0.1) & (scl_raw == 5)] = 0
    
    # ЦЕЛ: Клас 1 (Фитопланктон/Водорасли) -> NDVI > 0.01 (В рамките на езерото)
    # Това е най-важното правило. Ако NDVI е положително, значи има хлорофил (растителност),
    # дори SCL да го е класифицирал като вода. Презаписваме предишните етикети.
    labels[ndvi > 0.01] = 1
    
    # 5. Семплиране (Извличане на ограничен брой точки за всеки клас)
    new_samples = []
    classes = [0, 1, 2]
    # Вземаме до 1000 пиксела от всеки клас, за да балансираме набора от данни
    SAMPLES_PER_CLASS = 1000  
    
    print(" Семплиране на точките...")
    for c in classes:
        # Намиране на индексите (X, Y) на всички пиксели, отговарящи на съответния клас
        candidates = np.where(labels == c)
        n_candidates = len(candidates[0])
        print(f"  Клас {c} кандидати: {n_candidates}")
        
        if n_candidates == 0:
            print(f"   Внимание: Няма кандидати за клас {c}")
            continue
            
        # Случаен избор (Random sample) на пиксели
        n_samples = min(n_candidates, SAMPLES_PER_CLASS)
        indices = np.random.choice(n_candidates, n_samples, replace=False)
        selected_y = candidates[0][indices]
        selected_x = candidates[1][indices]
        
        # Добавяне на избраните пиксели и техните стойности в списъка
        for y, x in zip(selected_y, selected_x):
            new_samples.append({
                'class_id': c,
                'band_1': int(b2_calib[y, x]),
                'band_2': int(b3_calib[y, x]),
                'band_3': int(b4_calib[y, x]),
                'band_4': int(b8_calib[y, x]),
                'ndvi': round(float(ndvi[y, x]), 4),
                'ndwi': round(float(ndwi[y, x]), 4)
            })

    # 6. Запазване на резултатите в CSV файл
    if not new_samples:
        print("Не са извлечени никакви проби.")
        return

    print(f"Извлечени са общо {len(new_samples)} проби. Записване в {OUTPUT_CSV}...")
    # Създаване на DataFrame и експорт в CSV без индекс колона
    df = pd.DataFrame(new_samples)
    df.to_csv(OUTPUT_CSV, index=False)
    print("Готово.")

if __name__ == "__main__":
    extract_data()
