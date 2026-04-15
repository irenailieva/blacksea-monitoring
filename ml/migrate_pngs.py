import os
import glob
from image_processor import bake_png

inference_dir = "data/inference"
tifs = glob.glob(os.path.join(inference_dir, "*_classification.tif"))

print(f"🔍 Found {len(tifs)} classification TIFFs. Starting migration...")

for tif in tifs:
    png = tif.replace(".tif", ".png")
    if not os.path.exists(png):
        try:
            bake_png(tif, png)
        except Exception as e:
            print(f"❌ Failed to bake {tif}: {e}")
    else:
        print(f"⏭️ {png} already exists. Skipping.")

print("🏁 Migration complete.")
