"""Cloud-Native Sentinel-2 L2A STAC & Elevation Feature Sampler for Hargeisa.

Queries the public Element84 Earth Search STAC API (no authentication required)
to sample real Sentinel-2 Level-2A surface reflectance bands (B04 Red, B08 NIR,
B11 SWIR-1) across 2020 and 2026 dry-season epochs, computes NDBI, NDVI, and
Delta-NDBI, and interpolates terrain elevation and slope gradient (%) from the
cached Open-Meteo SRTM elevation grid (data/raw/hargeisa_elevation_data.json).
"""

import json
import os
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from scipy.interpolate import RegularGridInterpolator
import requests

STAC_SEARCH_URL = "https://earth-search.aws.element84.com/v1/search"
HARGEISA_BBOX = [43.96, 9.50, 44.14, 9.62]


def load_elevation_interpolator(elev_json_path: str):
    """Build bilinear interpolator and slope gradient grid from cached 9x9 SRTM JSON."""
    with open(elev_json_path, "r", encoding="utf-8") as f:
        elev_raw = json.load(f)["elevation"]

    lats = np.array([9.5 + (i * 0.012) for i in range(9)])
    lons = np.array([43.95 + (j * 0.024) for j in range(9)])
    grid = np.array(elev_raw, dtype=float).reshape(9, 9)

    # Approximate metric grid spacing at 9.55 N latitude
    dy_m = 0.012 * 110574.0
    dx_m = 0.024 * 111320.0 * np.cos(np.radians(9.55))
    grad_y, grad_x = np.gradient(grid, dy_m, dx_m)
    slope_pct_grid = np.hypot(grad_x, grad_y) * 100.0

    elev_interp = RegularGridInterpolator((lats, lons), grid, bounds_error=False, fill_value=None)
    slope_interp = RegularGridInterpolator((lats, lons), slope_pct_grid, bounds_error=False, fill_value=None)
    return elev_interp, slope_interp


def find_best_sentinel2_item(start_date: str, end_date: str, max_cloud: float = 10.0) -> dict:
    """Query Element84 STAC for the lowest-cloud Sentinel-2 L2A scene covering Hargeisa."""
    payload = {
        "collections": ["sentinel-2-l2a"],
        "bbox": HARGEISA_BBOX,
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "limit": 25,
        "query": {"eo:cloud_cover": {"lt": max_cloud}},
    }
    resp = requests.post(STAC_SEARCH_URL, json=payload, timeout=30)
    resp.raise_for_status()
    features = resp.json().get("features", [])
    if not features:
        raise RuntimeError(f"No Sentinel-2 L2A scenes found for {start_date}..{end_date}")
    # Prefer scenes whose bbox fully covers Hargeisa listings and have minimal cloud cover
    covering = [
        ft for ft in features
        if ft["bbox"][0] <= 44.01 and ft["bbox"][2] >= 44.11
        and ft["bbox"][1] <= 9.51 and ft["bbox"][3] >= 9.59
    ]
    pool = covering if covering else features
    pool.sort(key=lambda ft: ft["properties"].get("eo:cloud_cover", 100.0))
    return pool[0]


def sample_stac_item_bands(item: dict, coords_latlon: list) -> pd.DataFrame:
    """Sample Red (B04), NIR (B08), and SWIR-1 (B11) COG assets at (lat, lon) points."""
    assets = item["assets"]
    band_urls = {
        "red": assets["red"]["href"],
        "nir": assets["nir"]["href"],
        "swir16": assets["swir16"]["href"],
    }
    sampled = {}
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", AWS_NO_SIGN_REQUEST="YES"):
        for band_name, url in band_urls.items():
            with rasterio.open(url) as src:
                transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
                xy_pts = [transformer.transform(lon, lat) for lat, lon in coords_latlon]
                vals = [float(v[0]) for v in src.sample(xy_pts)]
                sampled[band_name] = np.array(vals, dtype=float)

    # Sentinel-2 L2A COGs are scaled integers (divide by 10000; guard zeros)
    nir = sampled["nir"]
    swir = sampled["swir16"]
    red = sampled["red"]

    ndbi = np.where((swir + nir) > 0, (swir - nir) / (swir + nir), 0.0)
    ndvi = np.where((nir + red) > 0, (nir - red) / (nir + red), 0.0)
    return pd.DataFrame({
        "ndbi": np.round(ndbi, 6),
        "ndvi": np.round(ndvi, 6),
        "scene_id": item["id"],
        "scene_date": item["properties"].get("datetime", "")[:10],
        "cloud_cover_pct": item["properties"].get("eo:cloud_cover", None),
    })


def extract_and_cache_features(
    listings_csv: str = "data/raw/real_market_listings.csv",
    elev_json: str = "data/raw/hargeisa_elevation_data.json",
    out_csv: str = "data/raw/hargeisa_sentinel2_features.csv",
) -> pd.DataFrame:
    """Extract real Sentinel-2 (2020 vs 2026) NDBI/NDVI and SRTM elevation/slope for all points."""
    df = pd.read_csv(listings_csv)
    coords = list(zip(df["lat"].values, df["lon"].values))

    elev_interp, slope_interp = load_elevation_interpolator(elev_json)
    pts_arr = np.column_stack([df["lat"].values, df["lon"].values])
    elev_m = np.round(elev_interp(pts_arr), 2)
    slope_pct = np.round(slope_interp(pts_arr), 3)

    print("Querying Element84 STAC for dry-season Sentinel-2 L2A 2020 & 2026 scenes...")
    item_2020 = find_best_sentinel2_item("2020-01-01", "2020-03-31", max_cloud=10.0)
    item_2026 = find_best_sentinel2_item("2026-01-01", "2026-03-31", max_cloud=10.0)
    print(f"  2020 scene: {item_2020['id']} ({item_2020['properties'].get('datetime','')[:10]}, cloud={item_2020['properties'].get('eo:cloud_cover')}%)")
    print(f"  2026 scene: {item_2026['id']} ({item_2026['properties'].get('datetime','')[:10]}, cloud={item_2026['properties'].get('eo:cloud_cover')}%)")

    s2_2020 = sample_stac_item_bands(item_2020, coords)
    s2_2026 = sample_stac_item_bands(item_2026, coords)

    out_df = df.copy()
    out_df["ndbi_2020"] = s2_2020["ndbi"]
    out_df["ndvi_2020"] = s2_2020["ndvi"]
    out_df["ndbi_2026"] = s2_2026["ndbi"]
    out_df["ndvi_2026"] = s2_2026["ndvi"]
    out_df["delta_ndbi"] = np.round(s2_2026["ndbi"] - s2_2020["ndbi"], 6)
    out_df["elevation_m"] = elev_m
    out_df["slope_pct"] = slope_pct
    out_df["scene_2020"] = s2_2020["scene_id"]
    out_df["scene_2026"] = s2_2026["scene_id"]

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    out_df.to_csv(out_csv, index=False)
    print(f"Saved {len(out_df)} real Sentinel-2 + SRTM records to {out_csv}")
    return out_df


if __name__ == "__main__":
    extract_and_cache_features()
