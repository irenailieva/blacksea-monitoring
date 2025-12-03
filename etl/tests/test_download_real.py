import os
import sys
from loguru import logger

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from flows.downloader import download_data

def test_real_download():
    # Configuration for testing
    aoi = {
        "bbox": [27.85, 43.20, 27.95, 43.25]  # Varna Bay area
    }
    time_range = {
        "start_date": "2024-06-01",
        "end_date": "2024-06-30"
    }
    output_dir = "test_out"
    
    logger.info("Starting real download test...")
    try:
        result_path = download_data(aoi, time_range, output_dir, mode="real")
        
        if os.path.exists(result_path):
            logger.success(f"Test passed! File downloaded to: {result_path}")
            # Verify it's a valid file (basic check)
            if os.path.getsize(result_path) > 0:
                logger.info("File size is greater than 0.")
            else:
                logger.error("File is empty.")
        else:
            logger.error("Test failed! File was not created.")
            
    except Exception as e:
        logger.exception(f"Test failed with exception: {e}")

if __name__ == "__main__":
    test_real_download()
