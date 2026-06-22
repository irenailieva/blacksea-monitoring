import os
from pathlib import Path
from model import load_model
from image_processor import process_scene

def run_inference():
    base_dir = Path("/app/data/inference")
    output_path = base_dir / "full_vaya_classification.tif"
    artifacts_dir = Path("/app/artifacts")

    prefix = "sentinel2_S2C_35TNH_20260615_0_L2A"
    
    band_paths = {
        'b2': str(base_dir / f"{prefix}_b2.tif"),
        'b3': str(base_dir / f"{prefix}_b3.tif"),
        'b4': str(base_dir / f"{prefix}_b4.tif"),
        'b8': str(base_dir / f"{prefix}_b8.tif"),
        'scl': str(base_dir / f"{prefix}_scl.tif")
    }

    print("Checking files...")
    for b, p in band_paths.items():
        if not os.path.exists(p):
            print(f"Error: Missing file {p}")
            return
    print("All files found.")

    print("Loading models...")
    model = load_model(artifacts_dir)

    print(f"Starting classification for {prefix}...")
    process_scene(band_paths, str(output_path), model)
    print("Done!")

if __name__ == "__main__":
    run_inference()
