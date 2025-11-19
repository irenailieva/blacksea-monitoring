import requests
from pathlib import Path
from prefect import task

COPERNICUS_URL = "https://dataspace.copernicus.eu/odata/v1/Products"

@task
def download_sentinel(product_id: str, output_dir: str) -> str:
    """
    Изтегля Sentinel-2 SAFE файл чрез Copernicus Data Space API (OData).
    """
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    url = f"{COPERNICUS_URL}('{product_id}')/$value"

    out_file = Path(output_dir) / f"{product_id}.zip"
    response = requests.get(url, stream=True)

    if response.status_code != 200:
        raise RuntimeError(f"Download failed: {response.text}")

    with open(out_file, "wb") as f:
        for chunk in response.iter_content(1024 * 1024):
            f.write(chunk)

    return str(out_file)
