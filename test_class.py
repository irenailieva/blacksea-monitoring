import rasterio
import numpy as np
src=rasterio.open('/app/data/inference/sentinel2_S2C_35TNH_20260615_0_L2A_job126_0_classification.tif')
data=src.read(1)
u,c=np.unique(data[data!=255], return_counts=True)
print('Classification TIF Unique:', u)
print('Classification TIF Counts:', c)
