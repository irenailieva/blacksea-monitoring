import glob, rasterio, numpy as np
f = glob.glob('/app/data/inference/*.tif')[-1]
src = rasterio.open(f)
data = src.read(1)
u, c = np.unique(data[data!=255], return_counts=True)
print('TIF Unique:', u)
print('TIF Counts:', c)
