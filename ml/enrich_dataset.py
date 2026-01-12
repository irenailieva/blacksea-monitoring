import pandas as pd
import numpy as np
from pathlib import Path

DATA_PATH = Path(__file__).parent / "dataset.csv"

def calculate_ndvi(nir, red):
    denominator = nir + red
    return np.where(denominator != 0, (nir - red) / denominator, 0.0)

def calculate_ndwi(green, nir):
    denominator = green + nir
    return np.where(denominator != 0, (green - nir) / denominator, 0.0)

def enrich():
    print(f"Reading {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    # Check if exists
    if 'ndvi' in df.columns and 'ndwi' in df.columns:
        print("Dataset already contains ndvi and ndwi. Skipping.")
        return

    print("Calculating indices...")
    # band_1=Blue, band_2=Green, band_3=Red, band_4=NIR
    green = df['band_2'].values.astype(float)
    red = df['band_3'].values.astype(float)
    nir = df['band_4'].values.astype(float)

    df['ndvi'] = calculate_ndvi(nir, red)
    df['ndwi'] = calculate_ndwi(green, nir)

    # Round to reasonable precision (e.g. 4 decimals)
    df['ndvi'] = df['ndvi'].round(4)
    df['ndwi'] = df['ndwi'].round(4)

    print(f"Saving enriched dataset to {DATA_PATH}...")
    df.to_csv(DATA_PATH, index=False)
    print("Done.")
    
    # Verify
    print("New columns:", df.columns.tolist())
    print(df.head())

if __name__ == "__main__":
    enrich()
