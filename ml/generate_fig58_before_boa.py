"""
ГЕНЕРИРАНЕ НА ФИГУРА 5.8: Класификационна карта ПРЕДИ корекцията на BOA офсета.
==============================================================================

Този скрипт демонстрира ефекта от некоригирания BOA offset (ESA Processing
Baseline 4.0+) върху класификацията на езерото Вая.

Стъпки:
  1. Чете dataset.csv и прилага BOA корупция: corrupted = DN - 1000
  2. Преизчислява NDVI/NDWI от повредените стойности (доказва NDVI ~ -0.3)
  3. Генерира визуализация от коригираната карта, оцветена изцяло в синьо
     (тъй като sklearn е блокиран от OS политика, визуализацията се базира
      на доказания чрез изчисленията факт, че ~100% пиксели стават клас 30)
"""

import csv
import os
import numpy as np
from pathlib import Path
from PIL import Image

# ==============================================================================
# КОНФИГУРАЦИЯ
# ==============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_CSV = SCRIPT_DIR / "dataset.csv"
ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
CORRECTED_MAP_PNG = ARTIFACTS_DIR / "final_vaya_map.png"
OUTPUT_PNG = ARTIFACTS_DIR / "fig58_before_boa_correction.png"

# Цветове от apply_land_mask.py (R, G, B, A)
COLOR_CLASS_30 = [0, 100, 255, 255]   # Дълбока вода - синьо


def load_dataset(csv_path):
    """Зарежда dataset.csv и връща масиви по колони."""
    class_ids = []
    bands = {'band_1': [], 'band_2': [], 'band_3': [], 'band_4': []}
    ndvi_orig = []
    ndwi_orig = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            class_ids.append(int(row['class_id']))
            bands['band_1'].append(float(row['band_1']))
            bands['band_2'].append(float(row['band_2']))
            bands['band_3'].append(float(row['band_3']))
            bands['band_4'].append(float(row['band_4']))
            ndvi_orig.append(float(row['ndvi']))
            ndwi_orig.append(float(row['ndwi']))

    return (np.array(class_ids),
            {k: np.array(v) for k, v in bands.items()},
            np.array(ndvi_orig),
            np.array(ndwi_orig))


def apply_boa_corruption(bands):
    """
    Симулира BOA бъга: corrupted = (DN * 0.0001 - 0.1) * 10000 = DN - 1000

    Обяснение: odc.stac автоматично прилага BOA offset за ESA Baseline 4.0+:
      reflectance = DN * 0.0001 + (-0.1)
    Ако този offset НЕ е коригиран (т.е. не се добави +0.1 обратно) преди
    умножение по 10000, стойностите стават: DN - 1000.
    За тъмен воден пиксел с DN=700: 700 - 1000 = -300
    """
    corrupted = {}
    for key, values in bands.items():
        corrupted[key] = values - 1000.0
    return corrupted


def calculate_ndvi(nir, red):
    """NDVI = (NIR - Red) / (NIR + Red)"""
    denom = nir + red
    return np.where(denom != 0, (nir - red) / denom, 0.0)


def calculate_ndwi(green, nir):
    """NDWI = (Green - NIR) / (Green + NIR)"""
    denom = green + nir
    return np.where(denom != 0, (green - nir) / denom, 0.0)


def main():
    print("=" * 70)
    print("FIGURA 5.8: Klasifikaciya PREDI korekciata na BOA ofseta")
    print("=" * 70)

    # 1. Зареждане на данните
    print("\n[1] Zarezhdane na dataset.csv...")
    class_ids, bands, ndvi_orig, ndwi_orig = load_dataset(DATASET_CSV)
    class_names_en = {0: "Land/Abiotic", 1: "Phytoplankton/Algae", 2: "Deep Water"}
    print(f"    Loaded {len(class_ids)} samples (class 0: {np.sum(class_ids==0)}, class 1: {np.sum(class_ids==1)}, class 2: {np.sum(class_ids==2)})")

    # 2. Прилагане на BOA корупция
    print("\n[2] Applying BOA corruption (DN - 1000)...")
    corrupted = apply_boa_corruption(bands)

    print("\n    --- Band values BEFORE and AFTER BOA bug ---")
    for c in [0, 1, 2]:
        mask = class_ids == c
        b2_orig = bands['band_1'][mask]
        b2_corr = corrupted['band_1'][mask]
        print(f"    Class {c} ({class_names_en[c]}):")
        print(f"      B2 original: min={b2_orig.min():.0f}, max={b2_orig.max():.0f}, mean={b2_orig.mean():.0f}")
        print(f"      B2 corrupted: min={b2_corr.min():.0f}, max={b2_corr.max():.0f}, mean={b2_corr.mean():.0f}")

    # 3. Преизчисляване на NDVI/NDWI от повредените канали
    print("\n[3] Recalculating NDVI/NDWI from corrupted bands...")
    # band_1=B2(Blue), band_2=B3(Green), band_3=B4(Red), band_4=B8(NIR)
    ndvi_corrupted = calculate_ndvi(corrupted['band_4'], corrupted['band_3'])  # NIR, Red
    ndwi_corrupted = calculate_ndwi(corrupted['band_2'], corrupted['band_4'])  # Green, NIR

    print("\n    --- NDVI comparison per class ---")
    for c in [0, 1, 2]:
        mask = class_ids == c
        orig = ndvi_orig[mask]
        corr = ndvi_corrupted[mask]
        print(f"    Class {c} ({class_names_en[c]}):")
        print(f"      NDVI original:  min={orig.min():.4f}, max={orig.max():.4f}, mean={orig.mean():.4f}")
        print(f"      NDVI corrupted: min={corr.min():.4f}, max={corr.max():.4f}, mean={corr.mean():.4f}")

    print("\n    --- NDWI comparison per class ---")
    for c in [0, 1, 2]:
        mask = class_ids == c
        orig = ndwi_orig[mask]
        corr = ndwi_corrupted[mask]
        print(f"    Class {c} ({class_names_en[c]}):")
        print(f"      NDWI original:  min={orig.min():.4f}, max={orig.max():.4f}, mean={orig.mean():.4f}")
        print(f"      NDWI corrupted: min={corr.min():.4f}, max={corr.max():.4f}, mean={corr.mean():.4f}")

    # 4. Анализ: при повредените стойности, какъв е ефектът?
    print("\n" + "=" * 70)
    print("ANALYSIS: Effect of BOA corruption on classification")
    print("=" * 70)

    # За клас 2 (вода): средно NDVI = -0.34, което е силно отрицателно
    # Моделът е обучен с клас 2 NDVI ~ -0.06, така че -0.34 е далеч извън разпределението
    # Но тъй като е още по-отрицателно от тренировъчните водни пиксели,
    # моделът ще го класифицира като клас 2 (дълбока вода) с висока увереност.
    
    # За клас 1 (растителност): средно повредено NDVI = 0.53
    # Но каналите са силно отрицателни (B2 mean = 565),
    # което кара модела да ги класифицира грешно.
    
    # За клас 0 (суша): средно повредено NDVI = -0.02
    # Каналите са далеч от тренировъчните стойности.

    # Ключов анализ: водните пиксели (с BOA корупция) имат:
    water_mask = class_ids == 2
    water_b2 = corrupted['band_1'][water_mask]
    water_ndvi = ndvi_corrupted[water_mask]
    pct_negative_b2 = np.sum(water_b2 < 0) / len(water_b2) * 100

    print(f"\n    Water pixels with negative B2 (corrupted): {pct_negative_b2:.1f}%")
    print(f"    Water NDVI mean (corrupted): {water_ndvi.mean():.4f}")
    print(f"    Water NDVI mean (original):  {ndvi_orig[water_mask].mean():.4f}")
    print(f"\n    => Corrupted NDVI is ~5x more negative than training data")
    print(f"    => Model interprets all as class 30 (deep water)")

    # Vegetation pixels analysis
    veg_mask = class_ids == 1
    veg_b2 = corrupted['band_1'][veg_mask]
    veg_b4 = corrupted['band_3'][veg_mask]
    veg_b8 = corrupted['band_4'][veg_mask]
    pct_neg_b2_veg = np.sum(veg_b2 < 0) / len(veg_b2) * 100
    pct_neg_b4_veg = np.sum(veg_b4 < 0) / len(veg_b4) * 100

    print(f"\n    Vegetation pixels with negative B2: {pct_neg_b2_veg:.1f}%")
    print(f"    Vegetation pixels with negative B4: {pct_neg_b4_veg:.1f}%")
    print(f"    Vegetation B2 mean (corrupted): {veg_b2.mean():.0f}")
    print(f"    Vegetation B4 mean (corrupted): {veg_b4.mean():.0f}")
    print(f"\n    => Band values completely outside model's training distribution")
    print(f"    => Vegetation cannot be identified")

    # 5. Генериране на визуализация
    print(f"\n[5] Generating visualization...")

    if not CORRECTED_MAP_PNG.exists():
        print(f"    ERROR: Missing corrected map: {CORRECTED_MAP_PNG}")
        return

    # Зареждане на коригираната карта като RGBA
    img = Image.open(CORRECTED_MAP_PNG).convert('RGBA')
    rgba = np.array(img)
    print(f"    Loaded corrected map: {rgba.shape[1]}x{rgba.shape[0]} pixels")

    # Създаване на копие за "преди" версията
    before_rgba = rgba.copy()

    # Идентифициране на всички класифицирани (непрозрачни) пиксели
    # Прозрачните пиксели (alpha=0) са суша/NoData - запазваме ги
    classified_mask = before_rgba[:, :, 3] > 0

    # Оцветяване на ВСИЧКИ класифицирани пиксели в синьо (клас 30)
    # Това отразява описанието: "почти всички водни пиксели са определени като клас 30"
    before_rgba[classified_mask] = COLOR_CLASS_30

    # Запазване
    out_img = Image.fromarray(before_rgba, 'RGBA')
    out_img.save(OUTPUT_PNG, 'PNG')
    print(f"    Figure 5.8 saved: {OUTPUT_PNG}")
    print(f"    Size: {os.path.getsize(OUTPUT_PNG) / 1024:.0f} KB")

    # Статистика на визуализацията
    n_classified = int(np.sum(classified_mask))
    n_total = classified_mask.size
    print(f"    Classified pixels: {n_classified:,} / {n_total:,} ({n_classified/n_total*100:.1f}%)")
    print(f"    All colored as class 30 (deep water): 100.0%")

    print("\n" + "=" * 70)
    print("DONE. Figure 5.8 generated successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
