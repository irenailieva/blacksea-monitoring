import os
from pathlib import Path
from model import load_model
from image_processor import process_scene

def run_inference():
    # Paths
    # Logic: we run inside docker, so path is /app/data/inference
    base_dir = Path("/app/data/inference")
    output_path = base_dir / "output_classification.tif"
    artifacts_dir = Path("/app/artifacts")

    # Define band paths
    band_paths = {
        'b2': str(base_dir / "T35TNH_20250910T085721_B02_10m.jp2"),
        'b3': str(base_dir / "T35TNH_20250910T085721_B03_10m.jp2"),
        'b4': str(base_dir / "T35TNH_20250910T085721_B04_10m.jp2"),
        'b8': str(base_dir / "T35TNH_20250910T085721_B08_10m.jp2"),
        'scl': str(base_dir / "T35TNH_20250910T085721_SCL_20m.jp2")
    }

    # Verify files exist
    for b, p in band_paths.items():
        if not os.path.exists(p):
            print(f"Error: Required file not found: {p}")
            return

    print("Loading model...")
    try:
        model = load_model(artifacts_dir)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    print("Running inference...")
    try:
        process_scene(band_paths, str(output_path), model)
    except Exception as e:
        print(f"Error processing scene: {e}")
        return
    
    print(f"Done.")

if __name__ == "__main__":
    run_inference()
