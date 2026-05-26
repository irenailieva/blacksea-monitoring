import pandas as pd
import numpy as np
from pathlib import Path

# ==============================================================================
# СКРИПТ ЗА ОБОГАТЯВАНЕ НА ДАННИ (ENRICH DATASET)
# Този скрипт прочита съществуващия набор от данни (CSV) и добавя нови 
# изчислени спектрални индекси като NDVI (Нормализиран диференциален вегетационен индекс)
# и NDWI (Нормализиран диференциален воден индекс).
# ==============================================================================

# Задаване на пътя до файла с данни
DATA_PATH = Path(__file__).parent / "dataset.csv"

def calculate_ndvi(nir, red):
    """
    Изчислява NDVI (Normalized Difference Vegetation Index).
    Формула: (NIR - RED) / (NIR + RED)
    NDVI се използва за идентифициране на растителност. Стойности близки до 1
    означават гъста и здрава растителност.
    """
    denominator = nir + red
    # np.where предотвратява деление на нула. Ако знаменателят не е 0, смятаме формулата,
    # иначе връщаме 0.0.
    return np.where(denominator != 0, (nir - red) / denominator, 0.0)

def calculate_ndwi(green, nir):
    """
    Изчислява NDWI (Normalized Difference Water Index).
    Формула: (GREEN - NIR) / (GREEN + NIR)
    NDWI се използва за идентифициране на водни обекти. Стойности > 0
    обикновено индикират наличието на вода.
    """
    denominator = green + nir
    # Аналогична проверка за деление на нула, както при NDVI.
    return np.where(denominator != 0, (green - nir) / denominator, 0.0)

def enrich():
    """
    Главна функция за обогатяване на набора от данни.
    """
    print(f"Четене на данните от {DATA_PATH}...")
    # Зареждане на данните в pandas DataFrame
    df = pd.read_csv(DATA_PATH)
    
    # Проверка дали данните вече са били обогатени.
    # Това предотвратява повторни изчисления, ако скриптът бъде стартиран два пъти.
    if 'ndvi' in df.columns and 'ndwi' in df.columns:
        print("Данните вече съдържат ndvi и ndwi. Пропускане на стъпката.")
        return

    print("Изчисляване на спектрални индекси...")
    # Извличане на стойностите за отделните спектрални канали.
    # В Sentinel-2: band_2 = Синьо (Blue), band_3 = Зелено (Green), band_4 = Червено (Red), band_8 = Близък инфрачервен (NIR).
    # Забележка: В някои конфигурации band_4 може да е NIR, затова се съобразяваме с текущото именуване в CSV файла.
    green = df['band_2'].values.astype(float)
    red = df['band_3'].values.astype(float)
    nir = df['band_4'].values.astype(float)

    # Прилагане на функциите за изчисление върху колоните и създаване на нови такива.
    df['ndvi'] = calculate_ndvi(nir, red)
    df['ndwi'] = calculate_ndwi(green, nir)

    # Закръгляване на стойностите до разумна прецизност (например 4 знака след десетичната запетая),
    # за да се спести памет и да бъде по-четливо.
    df['ndvi'] = df['ndvi'].round(4)
    df['ndwi'] = df['ndwi'].round(4)

    # Записване на обогатения DataFrame обратно в същия CSV файл.
    print(f"Запазване на обогатените данни в {DATA_PATH}...")
    df.to_csv(DATA_PATH, index=False)
    print("Готово.")
    
    # Проверка (Verification): Извеждане на малко информация в конзолата, за да сме сигурни, че всичко е наред.
    print("Нови колони:", df.columns.tolist())
    print(df.head())

# Стартиране на главната функция, ако скриптът се изпълнява директно
if __name__ == "__main__":
    enrich()
