import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling
import numpy as np
import pandas as pd
from pathlib import Path
import time
import utils

# -- КОНФИГУРАЦИЯ НА ПЪТИЩАТА --
BASE_DIR = Path(r"C:\Users\irena\Downloads\pomorie-uniform-ndvi")
OUTPUT_CSV = Path(__file__).parent / "dataset.csv"

# Пътища до отделните спектрални канали (Bands) за Pomorie
B2_PATH = BASE_DIR / "T35TNH_20240610T085559_B02_10m.jp2"
B3_PATH = BASE_DIR / "T35TNH_20240610T085559_B03_10m.jp2"
B4_PATH = BASE_DIR / "T35TNH_20240610T085559_B04_10m.jp2"
B8_PATH = BASE_DIR / "T35TNH_20240610T085559_B08_10m.jp2"
SCL_PATH = BASE_DIR / "T35TNH_20240610T085559_SCL_20m.jp2"

# Поморие залив
POMORIE_ROI_WGS84 = (27.5500, 42.5000, 27.6800, 42.6200)

def extract_data():
    start_time = time.time()
    print("--- Извличане на данни за Морски Фитопланктон (Pomorie) ---")
    
    with rasterio.open(B2_PATH) as src:
        left, bottom, right, top = transform_bounds("EPSG:4326", src.crs, *POMORIE_ROI_WGS84)
        window = from_bounds(left, bottom, right, top, transform=src.transform)

    with rasterio.open(B2_PATH) as src_b2, \
         rasterio.open(B3_PATH) as src_b3, \
         rasterio.open(B4_PATH) as src_b4, \
         rasterio.open(B8_PATH) as src_b8, \
         rasterio.open(SCL_PATH) as src_scl:
         
        b2 = src_b2.read(1, window=window).astype(float)
        b3 = src_b3.read(1, window=window).astype(float)
        b4 = src_b4.read(1, window=window).astype(float)
        b8 = src_b8.read(1, window=window).astype(float)
        
        scl_window = from_bounds(left, bottom, right, top, transform=src_scl.transform)
        scl_raw = src_scl.read(
            1, 
            window=scl_window,
            out_shape=(b2.shape[0], b2.shape[1]),
            resampling=Resampling.nearest
        )

    # Прилагане на BOA Offset корекция
    features = utils.prepare_features(b2.flatten(), b3.flatten(), b4.flatten(), b8.flatten())
    b2_calib = features[:, 0].reshape(b2.shape)
    b3_calib = features[:, 1].reshape(b3.shape)
    b4_calib = features[:, 2].reshape(b4.shape)
    b8_calib = features[:, 3].reshape(b8.shape)
    ndvi = features[:, 4].reshape(b2.shape)
    ndwi = features[:, 5].reshape(b2.shape)
    
    labels = np.full(ndvi.shape, -1, dtype=int)
    
    # ЦЕЛ: Клас 3 (Морски Фитопланктон / Coccolithophore Bloom)
    # Има леко положително NDVI (0.02 - 0.2) и се намира във вода (SCL 6)
    labels[(ndvi > 0.02) & (ndvi < 0.2) & (scl_raw == 6)] = 3
    
    new_samples = []
    c = 3
    SAMPLES_PER_CLASS = 1500  # Extract more to balance the dataset against the others
    
    candidates = np.where(labels == c)
    n_candidates = len(candidates[0])
    print(f"  Клас {c} кандидати: {n_candidates}")
    
    if n_candidates > 0:
        n_samples = min(n_candidates, SAMPLES_PER_CLASS)
        indices = np.random.choice(n_candidates, n_samples, replace=False)
        selected_y = candidates[0][indices]
        selected_x = candidates[1][indices]
        
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

    if not new_samples:
        print("Не са извлечени никакви проби.")
        return

    print(f"Извлечени са {len(new_samples)} нови проби. Добавяне към {OUTPUT_CSV}...")
    
    # Зареждане на стария CSV и добавяне (append)
    if OUTPUT_CSV.exists():
        existing_df = pd.read_csv(OUTPUT_CSV)
        # Remove any existing class 3 to avoid duplicates
        existing_df = existing_df[existing_df['class_id'] != 3]
        new_df = pd.DataFrame(new_samples)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = pd.DataFrame(new_samples)
        
    combined_df.to_csv(OUTPUT_CSV, index=False)
    print("Готово. Клас 3 е добавен!")

if __name__ == "__main__":
    extract_data()
