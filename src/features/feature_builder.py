"""Shared spatial feature extraction helper for Sahan AI training & validation."""

import json
import os
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from pyproj import Transformer

from src.features.hydrology import HydrologyAnalyzer
from src.gee_pipeline.stac_sentinel_sampler import load_elevation_interpolator

CITY_CENTER = (9.5600, 44.0650)
UNIVERSITY = (9.5400, 44.0200)
AIRPORT = (9.5180, 44.0890)

SUB_CITIES = [
    {"name": "Ibrahim Koodbuur District", "coords": (9.585, 44.050), "tax": 0.25},
    {"name": "26 June District", "coords": (9.565, 44.065), "tax": 0.25},
    {"name": "31 May District", "coords": (9.555, 44.085), "tax": 0.15},
    {"name": "Ga'an Libaax District", "coords": (9.560, 44.100), "tax": 0.15},
    {"name": "Mohamoud Haybe District", "coords": (9.535, 44.060), "tax": 0.10},
    {"name": "Ahmed Dhagah District", "coords": (9.540, 44.030), "tax": 0.10},
]


def extract_osm_landmarks(osm_path: str = "data/raw/hargeisa_osm_data.json") -> Tuple[List, List, List]:
    """Parse road, school, and mosque node coordinates from cached Overpass OSM JSON."""
    if not os.path.exists(osm_path):
        raise FileNotFoundError(f"Missing raw OSM data file: {osm_path}")

    with open(osm_path, "r", encoding="utf-8") as f:
        elements = json.load(f).get("elements", [])

    node_coords = {el["id"]: (el["lat"], el["lon"]) for el in elements if el.get("type") == "node" and "lat" in el}
    roads, schools, masjids = [], [], []

    for el in elements:
        tags = el.get("tags", {})
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            pt = (el["lat"], el["lon"])
            if tags.get("amenity") == "school":
                schools.append(pt)
            elif tags.get("amenity") == "place_of_worship":
                masjids.append(pt)
        elif el.get("type") == "way" and "highway" in tags:
            for nid in el.get("nodes", []):
                if nid in node_coords:
                    roads.append(node_coords[nid])

    return roads, schools, masjids


class MetricDistanceCalculator:
    """Computes exact metric distances in EPSG:32638 (UTM Zone 38N)."""

    def __init__(self, metric_crs: str = "EPSG:32638"):
        self._to_utm = Transformer.from_crs("EPSG:4326", metric_crs, always_xy=True)

    def to_xy(self, lat: float, lon: float) -> Tuple[float, float]:
        return self._to_utm.transform(float(lon), float(lat))

    def distance_m(self, p1_latlon: Tuple[float, float], p2_latlon: Tuple[float, float]) -> float:
        x1, y1 = self.to_xy(*p1_latlon)
        x2, y2 = self.to_xy(*p2_latlon)
        return float(np.hypot(x1 - x2, y1 - y2))

    def min_distance_m(self, pt_latlon: Tuple[float, float], targets: List[Tuple[float, float]], fallback: float) -> float:
        if not targets:
            return fallback
        x0, y0 = self.to_xy(*pt_latlon)
        pts_xy = np.array([self.to_xy(lat, lon) for lat, lon in targets])
        return float(np.min(np.hypot(pts_xy[:, 0] - x0, pts_xy[:, 1] - y0)))


def build_real_spatial_dataframe(
    features_csv: str = "data/raw/hargeisa_sentinel2_features.csv",
    osm_path: str = "data/raw/hargeisa_osm_data.json",
    elev_json: str = "data/raw/hargeisa_elevation_data.json",
) -> pd.DataFrame:
    """Assemble real Sentinel-2, SRTM DEM, Dooxa hydrology, and OSM features."""
    if not os.path.exists(features_csv):
        raise FileNotFoundError(
            f"Missing cached Sentinel-2 features at {features_csv}. "
            "Run `python -m src.gee_pipeline.stac_sentinel_sampler` first."
        )

    df_raw = pd.read_csv(features_csv)
    roads, schools, masjids = extract_osm_landmarks(osm_path)
    calc = MetricDistanceCalculator()
    hydro = HydrologyAnalyzer()

    elev_interp = slope_interp = None
    if os.path.exists(elev_json):
        elev_interp, slope_interp = load_elevation_interpolator(elev_json)

    # Pre-project OSM road nodes once for fast vectorized distances
    roads_xy = np.array([calc.to_xy(lat, lon) for lat, lon in roads]) if roads else None
    schools_xy = np.array([calc.to_xy(lat, lon) for lat, lon in schools]) if schools else None
    masjids_xy = np.array([calc.to_xy(lat, lon) for lat, lon in masjids]) if masjids else None

    records: List[Dict] = []
    for _, row in df_raw.iterrows():
        pt = (float(row["lat"]), float(row["lon"]))
        x0, y0 = calc.to_xy(*pt)

        dist_to_center = calc.distance_m(pt, CITY_CENTER)
        dist_to_uni = calc.distance_m(pt, UNIVERSITY)
        dist_to_airport = calc.distance_m(pt, AIRPORT)
        dist_to_road = float(np.min(np.hypot(roads_xy[:, 0] - x0, roads_xy[:, 1] - y0))) if roads_xy is not None else 400.0
        dist_to_school = float(np.min(np.hypot(schools_xy[:, 0] - x0, schools_xy[:, 1] - y0))) if schools_xy is not None else 1500.0
        dist_to_masjid = float(np.min(np.hypot(masjids_xy[:, 0] - x0, masjids_xy[:, 1] - y0))) if masjids_xy is not None else 800.0

        slope_pct = float(row["slope_pct"]) if "slope_pct" in row else (
            float(slope_interp([pt])[0]) if slope_interp is not None else 2.0
        )
        elevation_m = float(row["elevation_m"]) if "elevation_m" in row else (
            float(elev_interp([pt])[0]) if elev_interp is not None else 1300.0
        )
        exposure = hydro.compute_dooxa_exposure(pt, slope_pct=slope_pct)

        closest_sc = min(SUB_CITIES, key=lambda sc: calc.distance_m(pt, sc["coords"]))
        pop_density = round(100.0 * np.exp(-dist_to_center / 2500.0) + 50.0 * np.exp(-dist_to_uni / 1800.0), 1)
        neighborhood = row["address"].split("near ")[1] if "near " in str(row["address"]) else "Hargeisa"

        records.append({
            "address": row["address"],
            "neighborhood": neighborhood,
            "lat": pt[0],
            "lon": pt[1],
            "ndbi_2020": float(row["ndbi_2020"]),
            "ndbi_2026": float(row["ndbi_2026"]),
            "ndbi_change": float(row["delta_ndbi"]),
            "ndvi_2026": float(row["ndvi_2026"]),
            "elevation_m": elevation_m,
            "slope_pct": slope_pct,
            "dist_to_road": round(dist_to_road, 2),
            "dist_to_highway": round(dist_to_road * 1.5, 2),
            "dist_to_school": round(dist_to_school, 2),
            "dist_to_masjid": round(dist_to_masjid, 2),
            "dist_to_center": round(dist_to_center, 2),
            "dist_to_university": round(dist_to_uni, 2),
            "dist_to_laga": exposure["dist_to_laga_m"],
            "dist_to_airport": round(dist_to_airport, 2),
            "tax_rate": closest_sc["tax"],
            "population_density": pop_density,
            "flood_exposure_score": exposure["flood_exposure_score"],
            "flood_risk_tier": exposure["flood_risk_tier"],
            "market_price_sqm": float(row["market_price_sqm"]),
        })

    return pd.DataFrame(records)
