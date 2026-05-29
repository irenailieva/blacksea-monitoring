import pandas as pd, numpy as np
df = pd.read_csv('/app/dataset.csv')

print("=== Band ranges per class ===")
for cls in [0, 1, 2]:
    sub = df[df['class_id'] == cls]
    b1_mean = sub['band_1'].mean()
    b4_mean = sub['band_4'].mean()
    ndvi_mean = sub['ndvi'].mean()
    ndwi_mean = sub['ndwi'].mean()
    print(f"Class {cls}: band_1(B2)={b1_mean:.0f}  band_4(B8/NIR)={b4_mean:.0f}  ndvi={ndvi_mean:.3f}  ndwi={ndwi_mean:.3f}")

print()
print("=== NDVI/NDWI ranges per class ===")
for cls in [0, 1, 2]:
    sub = df[df['class_id'] == cls]
    ndvi_min = sub['ndvi'].min()
    ndvi_max = sub['ndvi'].max()
    ndwi_min = sub['ndwi'].min()
    ndwi_max = sub['ndwi'].max()
    print(f"Class {cls}: ndvi=[{ndvi_min:.3f}, {ndvi_max:.3f}]  ndwi=[{ndwi_min:.3f}, {ndwi_max:.3f}]")

print()
print("=== Column mapping in train.py ===")
print("train.py assigns: blue=band_1, green=band_2, red=band_3, nir=band_4")
print("BUT Sentinel-2 bands are: B2=Blue, B3=Green, B4=Red, B8=NIR")
print()
print("=== prepare_features band order check ===")
print("prepare_features(blue, green, red, nir) => [B2, B3, B4, B8, NDVI, NDWI]")
print("Training assigns: blue=band_1, green=band_2, red=band_3, nir=band_4")
print()
print("Dataset NDVI values (should be (NIR-RED)/(NIR+RED)):")
# Recompute to check
b_nir = df['band_4'].values.astype(float)
b_red = df['band_3'].values.astype(float)
recomputed_ndvi = (b_nir - b_red) / (b_nir + b_red + 1e-9)
stored_ndvi = df['ndvi'].values
print(f"  Stored ndvi mean:     {stored_ndvi.mean():.4f}")
print(f"  Recomputed ndvi mean: {recomputed_ndvi.mean():.4f}")
print(f"  Correlation: {np.corrcoef(stored_ndvi, recomputed_ndvi)[0,1]:.4f}")
