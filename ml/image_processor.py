import rasterio
from rasterio.enums import Resampling
import numpy as np
import cv2
import os
import time
from utils import prepare_features
from PIL import Image

# ==============================================================================
# ОБРАБОТКА НА ИЗОБРАЖЕНИЯ (IMAGE PROCESSOR)
# Този модул съдържа функции за прилагане на обучените ML модели върху
# сателитни снимки или качени от потребителя GeoTIFF файлове. 
# Основната цел е да се генерира карта на качеството на водата и да се 
# създадат визуализации (PNG) за frontend-а.
# ==============================================================================

def process_scene(band_paths: dict, output_path: str, model):
    """
    Генерира карта на качеството на водата от канали на Sentinel-2 (Bands).
    
    Аргументи:
        band_paths (dict): Речник с пътищата до файловете (b2, b3, b4, b8, scl).
        output_path (str): Път, където да бъде запазен резултантният TIF файл.
        model (WaterQualityModel): Инстанция на заредения ML модел за предсказване.
    """
    
    b2_path = band_paths.get('b2')
    b3_path = band_paths.get('b3')
    b4_path = band_paths.get('b4')
    b8_path = band_paths.get('b8')
    scl_path = band_paths.get('scl')

    # Проверка дали всички необходими файлове са подадени
    if not all([b2_path, b3_path, b4_path, b8_path, scl_path]):
        raise ValueError("Липсва един или повече задължителни пътища до каналите.")

    # 🚀 ОБРАБОТКА ПРИ РЪЧНО КАЧЕН ФАЙЛ (SINGLE FILE MANUAL UPLOAD)
    # Ако потребителят е качил единичен RGB/Мултиспектрален GeoTIFF (например от дрон),
    # бекендът подава един и същ файл за всички канали.
    is_single_file = (b2_path == b3_path == b4_path == b8_path == scl_path) and b2_path is not None
    
    if is_single_file:
        print(f"🔄 Обработка на единичен ръчно качен файл...")
        all_confidences = []  # Натрупване на увереностите от всички блокове
        with rasterio.open(b2_path) as src:
            # Копираме профила на изходното изображение и го настройваме за резултата
            profile = src.profile.copy()
            profile.update(driver='GTiff', dtype=rasterio.uint8, count=1, nodata=255)
            
            # Проверяваме дали изображението съдържа инфрачервен канал (NIR - обикновено 4-ти канал)
            has_nir = src.count >= 4
            
            # Отваряме изходния TIF файл за запис
            with rasterio.open(output_path, 'w', **profile) as dst:
                # Четем изображението блок по блок, за да не препълним RAM паметта (block_windows)
                for ji, window in src.block_windows(1):
                    # Картографиране на каналите според броя налични слоеве:
                    if src.count == 5:
                        # Sentinel-2 Composite: 1=Blue, 2=Green, 3=Red, 4=NIR, 5=SCL
                        b2 = src.read(1, window=window).astype('float32')
                        b3 = src.read(2, window=window).astype('float32')
                        b4 = src.read(3, window=window).astype('float32')
                        b8 = src.read(4, window=window).astype('float32')
                        scl_single = src.read(5, window=window)
                    else:
                        # В стандартен RGB образ: Канал 1 -> Червено (b4), Канал 2 -> Зелено (b3), Канал 3 -> Синьо (b2)
                        b4 = src.read(1, window=window).astype('float32')
                        b3 = src.read(2, window=window).astype('float32') if src.count >= 2 else b4
                        b2 = src.read(3, window=window).astype('float32') if src.count >= 3 else b3
                        
                        if has_nir:
                            b8 = src.read(4, window=window).astype('float32')
                        else:
                            # Ако липсва NIR (снимката е само RGB), използваме зеления канал като заместител.
                            b8 = b3
                        scl_single = None

                    if scl_single is not None:
                        # Ако имаме SCL маска (Sentinel-2 Composite), използваме я за филтриране
                        water_mask = (scl_single == 6)
                        binary_cloud_mask = np.isin(scl_single, [3, 8, 9, 10]).astype(np.uint8)
                        kernel = np.ones((15, 15), np.uint8)
                        dilated_cloud_mask = cv2.dilate(binary_cloud_mask, kernel, iterations=1)
                        target_mask = water_mask & ~dilated_cloud_mask.astype(bool)
                    else:
                        # Тъй като това е обикновена снимка (нямаме сателитна SCL маска),
                        # приемаме всички пиксели за валидни (target_mask).
                        target_mask = np.ones(b2.shape, dtype=bool)
                    # Създаваме празен блок за резултата, запълнен със стойност 255 (NoData)
                    result_block = np.full(b2.shape, 255, dtype=np.uint8)
                    
                    b2_water = b2[target_mask]
                    b3_water = b3[target_mask]
                    b4_water = b4[target_mask]
                    b8_water = b8[target_mask]
                    
                    # Подготовка на характеристиките за модела (изчислява индекси вътре)
                    X_water = prepare_features(b2_water, b3_water, b4_water, b8_water)
                    
                    if len(X_water) > 0:
                        # Предсказване на класовете и реалната увереност на модела
                        mapped_pred, conf_batch = model.predict_batch_with_confidence(X_water)
                        # Записваме резултата в съответните валидни пиксели на блока
                        result_block[target_mask] = mapped_pred
                        # Натрупване на увереностите за изчисляване на средната стойност
                        all_confidences.extend(conf_batch.tolist())
                        
                    # Записваме обработения блок във файла
                    dst.write(result_block, 1, window=window)
                    print(".", end="", flush=True)

        # Изчисляване на средната увереност от всички обработени пиксели
        single_avg_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        print(f"\n🎉 Единичният файл е генериран успешно: {output_path}")
        # 🔥 ГЕНЕРИРАНЕ НА PNG ИЗОБРАЖЕНИЕ С ВИСОКА ПРОИЗВОДИТЕЛНОСТ ЗА FRONTEND-А
        png_path = output_path.replace(".tif", ".png")
        stats = bake_png(output_path, png_path, avg_confidence=round(single_avg_conf, 1))
        return stats

    print(f"🔄 Обработка на сателитна сцена от Sentinel-2 (многофайлова)...")
    all_confidences = []  # Натрупване на увереностите от всички блокове

    # 1. Четене на SCL (Scene Classification Layer) и маскиране на облаци
    # Отваряме първия канал (B2), за да вземем точните размери (10m/px)
    with rasterio.open(b2_path) as src_ref:
        target_height = src_ref.height
        target_width = src_ref.width
        ref_profile = src_ref.profile.copy()

    with rasterio.open(scl_path) as src_scl:
        # SCL е 20m/px, затова го преоразмеряваме до 10m/px (target_height/width),
        # за да съвпада със спектралните канали.
        scl_full = src_scl.read(
            1,
            out_shape=(target_height, target_width), 
            resampling=Resampling.nearest 
        )

    # Създаване на маска за облаци (класове в SCL: 3, 8, 9, 10 означават облаци или сенки)
    binary_cloud_mask = np.isin(scl_full, [3, 8, 9, 10]).astype(np.uint8)
    # Разширяване (Dilate) на маската за облаците - често краищата на облаците са тънки
    # и SCL ги пропуска, затова "раздуваме" маската с 15x15 пиксела.
    kernel = np.ones((15, 15), np.uint8) 
    dilated_cloud_mask = cv2.dilate(binary_cloud_mask, kernel, iterations=1)

    # Whitelist подход: САМО пиксели с SCL клас 6 (Вода) са валидни.
    # Всички останали класове (0=NoData, 1=Наситени, 2=Тъмни зони,
    # 3=Облачни сенки, 4=Растителност, 5=Голи почви, 7=Некласифицирани,
    # 8-10=Облаци, 11=Сняг) се третират като невалидни.
    # Това предотвратява попадането на градски/тъмни пиксели (SCL 0, 1, 2)
    # в класификацията, където биват грешно разпознати като вода.
    water_mask = (scl_full == 6)
    # Крайна маска: невалидни са всички не-водни пиксели + зоните около облаци
    final_invalid_mask = ~water_mask | dilated_cloud_mask.astype(bool)

    print("✅ Генерирани са маските за облаци и суша.")

    # 2. Подготовка на профила за изходния файл
    profile = ref_profile.copy()
    profile.update(
        driver='GTiff',
        dtype=rasterio.uint8, 
        count=1, 
        nodata=255
    )

    # 3. Обработка на изображението на блокове (Block-by-Block Processing)
    print(f"🌍 Генериране на картата...")
    
    with rasterio.open(b2_path) as src_b2:
        # Определяне на глобални параметри за мащабиране
        sample_b2 = src_b2.read(1, out_shape=(1, src_b2.height // 10, src_b2.width // 10))
        valid_sample = sample_b2[sample_b2 > 0]
        data_max = np.nanmax(valid_sample) if len(valid_sample) > 0 else 0
        data_median = np.nanmedian(valid_sample) if len(valid_sample) > 0 else 0
        global_is_stac_scaled = bool(data_max <= 2.0)
        global_has_offset = bool(data_median >= 800)
        print(f"   [Инфо] Използва се глобален мащаб: STAC={global_is_stac_scaled}, Offset={global_has_offset}")

    with rasterio.open(b2_path) as src_b2, \
         rasterio.open(b3_path) as src_b3, \
         rasterio.open(b4_path) as src_b4, \
         rasterio.open(b8_path) as src_b8, \
         rasterio.open(output_path, 'w', **profile) as dst:
        
        # Обхождаме файловете на малки прозорци (blocks), което пести RAM
        for ji, window in src_b2.block_windows(1):
            
            # Четене на съответната част от общата невалидна маска
            row_start = window.row_off
            row_end = window.row_off + window.height
            col_start = window.col_off
            col_end = window.col_off + window.width
            
            invalid_chunk = final_invalid_mask[row_start:row_end, col_start:col_end]
            
            # Target Mask съдържа само валидните пиксели (инвертираме невалидната маска)
            target_mask = ~invalid_chunk
            
            # Ако в този блок няма нито един валиден пиксел (напр. изцяло суша), 
            # просто записваме празен блок (NoData = 255) и продължаваме към следващия.
            if not target_mask.any():
                empty_block = np.full((window.height, window.width), 255, dtype=rasterio.uint8)
                dst.write(empty_block, 1, window=window)
                continue

            # Четене на спектралните канали за текущия блок
            b2 = src_b2.read(1, window=window).astype('float32')
            b3 = src_b3.read(1, window=window).astype('float32')
            b4 = src_b4.read(1, window=window).astype('float32')
            b8 = src_b8.read(1, window=window).astype('float32')
            
            result_block = np.full(b2.shape, 255, dtype=np.uint8)
            
            # Извличане само на водните (валидни) пиксели
            b2_water = b2[target_mask]
            b3_water = b3[target_mask]
            b4_water = b4[target_mask]
            b8_water = b8[target_mask]
            
            # Подготовка на характеристиките [B2, B3, B4, B8, NDVI, NDWI]
            X_water = prepare_features(
                b2_water, b3_water, b4_water, b8_water,
                is_stac_scaled=global_is_stac_scaled,
                has_baseline_offset=global_has_offset
            )
            
            if len(X_water) > 0:
                # Предсказване на класа и реалната увереност на модела
                mapped_pred, conf_batch = model.predict_batch_with_confidence(X_water)
                result_block[target_mask] = mapped_pred
                # Натрупване на увереностите за крайната статистика
                all_confidences.extend(conf_batch.tolist())
            
            dst.write(result_block, 1, window=window)
            print(".", end="", flush=True)

    # Изчисляване на средната увереност от всички обработени пиксели
    scene_avg_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
    print(f"\n🎉 Картата е генерирана в {output_path} (средна увереност: {scene_avg_conf:.1f}%)")
    
    # 🔥 ГЕНЕРИРАНЕ НА PNG ИЗОБРАЖЕНИЕ
    png_path = output_path.replace(".tif", ".png")
    stats = bake_png(output_path, png_path, avg_confidence=round(scene_avg_conf, 1))
    return stats

def bake_png(tif_path: str, png_path: str, avg_confidence: float = 0.0):
    """
    Конвертира 1-канален TIF с класификация в 4-канален прозрачен RGBA PNG файл.
    Този файл се използва директно от frontend-а (Leaflet картата) за супер бърза визуализация.
    """
    print(f"📦 Създаване на PNG за уеб визуализация: {png_path}...")
    with rasterio.open(tif_path) as src:
        data = src.read(1).astype(np.float32)
        
        # Инициализация на RGBA масив (Височина, Ширина, 4)
        h, w = data.shape
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        
        # Здравословно картографиране на класовете към цветове (Robust Range Mapping).
        # Използват се интервали, за да се избегнат проблеми с floating-point грешки.
        
        # 1. Водорасли/Растителност (Изумрудено зелено #22c55e)
        # Класът от модела е 20.
        algae_mask = ((data >= 1.5) & (data < 2.5)) | ((data >= 15) & (data < 25.5))
        rgba[algae_mask] = [34, 197, 94, 255]
        
        # 2. Пясък/Абиотични (Златисто жълто #facc15)
        # Класът от модела е 10.
        sand_mask = ((data >= 0.5) & (data < 1.5)) | ((data >= 5) & (data < 15))
        rgba[sand_mask] = [250, 204, 21, 255]
        
        # 3. Дълбока вода (Синьо #1d4ed8)
        # Класът от модела е 30.
        water_mask = ((data >= 2.5) & (data < 5.0)) | ((data >= 25.5) & (data < 35))
        rgba[water_mask] = [29, 78, 216, 255]

        # 4. Морски фитопланктон / Coccolithophores (Тюркоазено #22d3ee)
        # Класът от модела е 40.
        bloom_mask = ((data >= 5.0) & (data < 6.0)) | ((data >= 35) & (data < 45))
        rgba[bloom_mask] = [34, 211, 238, 255]

        # Конвертиране на масива в PNG и запазване
        img = Image.fromarray(rgba, 'RGBA')
        img.save(png_path, 'PNG')
        print(f"✅ PNG е генериран успешно с {np.count_nonzero(algae_mask)} пиксела водорасли.")

        # Изчисляване на статистики за frontend-а.
        # Тъй като разделителната способност на Sentinel-2 е 10m/px, един пиксел се равнява на 10x10 = 100 m²
        return {
            "vegetation_area_m2": int(np.count_nonzero(algae_mask) * 100),
            "sand_area_m2": int(np.count_nonzero(sand_mask) * 100),
            "water_area_m2": int(np.count_nonzero(water_mask) * 100),
            "bloom_area_m2": int(np.count_nonzero(bloom_mask) * 100),
            "avg_confidence": avg_confidence  # Реална средна увереност от модела
        }
