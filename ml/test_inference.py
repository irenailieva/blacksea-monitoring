import sys
import os
from pathlib import Path
from model import load_model
from image_processor import process_scene

# Setup paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "inference"
OUTPUT_DIR = BASE_DIR / "data" / "output"
ARTIFACTS_DIR = BASE_DIR / "artifacts"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Define file paths
band_paths = {
    'b2': str(DATA_DIR / "mock_B02.tif"),
    'b3': str(DATA_DIR / "mock_B03.tif"),
    'b4': str(DATA_DIR / "mock_B04.tif"),
    'b8': str(DATA_DIR / "mock_B08.tif"),
    'scl': str(DATA_DIR / "mock_SCL.tif")
}

output_tif = str(OUTPUT_DIR / "classification_map.tif")

print("🔄 Loading model...")
try:
    model = load_model(ARTIFACTS_DIR)
    print("✅ Model loaded.")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    sys.exit(1)

print("🔄 Running inference...")
try:
    process_scene(band_paths, output_tif, model)
    print(f"✅ Inference successful! Output saved to: {output_tif}")
except Exception as e:
    print(f"❌ Inference failed: {e}")
    sys.exit(1)
