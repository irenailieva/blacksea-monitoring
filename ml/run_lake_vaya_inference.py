import os
from pathlib import Path
from model import load_model
from image_processor import process_scene

def run_inference():
    # Paths
    # Docker path: /app/data/inference/lake-vaya
    base_dir = Path("/app/data/inference/lake-vaya")
    output_path = base_dir / "output_classification.tif"
    artifacts_dir = Path("/app/artifacts")

    # Define band paths for the Lake Vaya scene (2023-06-06)
    band_paths = {
        'b2': str(base_dir / "T35TNH_20230606T085559_B02_10m.jp2"),
        'b3': str(base_dir / "T35TNH_20230606T085559_B03_10m.jp2"),
        'b4': str(base_dir / "T35TNH_20230606T085559_B04_10m.jp2"),
        'b8': str(base_dir / "T35TNH_20230606T085559_B08_10m.jp2"),
        'scl': str(base_dir / "T35TNH_20230606T085559_SCL_20m.jp2")
    }

    # Verify files exist
    print(f"Checking files in {base_dir}...")
    for b, p in band_paths.items():
        if not os.path.exists(p):
            print(f"Error: Required file not found: {p}")
            return
    print("All files found.")

    print("Loading model...")
    try:
        model = load_model(artifacts_dir)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    print(f"Running inference for Lake Vaya...")
    print(f"Output will be saved to: {output_path}")
    
    try:
        process_scene(band_paths, str(output_path), model)
    except Exception as e:
        print(f"Error processing scene: {e}")
        return

if __name__ == "__main__":
    run_inference()
