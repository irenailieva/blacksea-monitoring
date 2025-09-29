import csv
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

def save_csv(rows, fieldnames, out_path: Path) -> None:
    ensure_dir(out_path.parent)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    logger.info(f"CSV записан: {out_path}")

def save_geojson(features, out_path: Path) -> None:
    ensure_dir(out_path.parent)
    fc = {"type": "FeatureCollection", "features": features}
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    logger.info(f"GeoJSON записан: {out_path}")

def bbox_to_polygon(bbox):
    # bbox: [minLon, minLat, maxLon, maxLat]
    minx, miny, maxx, maxy = bbox
    return [
        [
            [minx, miny],
            [maxx, miny],
            [maxx, maxy],
            [minx, maxy],
            [minx, miny],
        ]
    ]

def tile_feature(tile_id: str, bbox, props: dict):
    return {
        "type": "Feature",
        "id": tile_id,
        "properties": props,
        "geometry": {
            "type": "Polygon",
            "coordinates": bbox_to_polygon(bbox)
        }
    }
