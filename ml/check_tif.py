import rasterio
import numpy as np
import sys

path = sys.argv[1]
with rasterio.open(path) as src:
    data = src.read(1)
    unique, counts = np.unique(data, return_counts=True)
    print(f"Values in {path}:")
    for v, c in zip(unique, counts):
        print(f"  Value {v}: {c} pixels")
