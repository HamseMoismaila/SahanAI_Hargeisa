"""Spatial Grid Indexing (UTM Zone 38N Fishnet + Uber H3 Discrete Global Grid System).

Provides both:
1. Metric square fishnet grids projected in EPSG:32638 (UTM Zone 38N) for
   traditional Euclidean proximity matrices and parcel-to-grid spatial joins.
2. Hierarchical Uber H3 hexagonal Discrete Global Grid Systems (DGGS) via `h3`
   to avoid square diagonal distortion and support multi-resolution urban sprawl
   and flash-flood exposure aggregation.
"""

from typing import Iterable, Optional, Tuple
import geopandas as gpd
import h3
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon, box


class SpatialJoiner:
    """Spatial grid generator and zonal feature aggregator for Hargeisa."""

    def __init__(self, crs: str = "EPSG:4326"):
        self.crs = crs
        # EPSG:32638 is UTM Zone 38N (metric CRS covering Somaliland / Hargeisa)
        self.metric_crs = "EPSG:32638"

    def create_grid(self, bounds: Tuple[float, float, float, float], cell_size: float = 500) -> gpd.GeoDataFrame:
        """Create a metric square fishnet grid over bounds = (minx, miny, maxx, maxy) in metric_crs."""
        minx, miny, maxx, maxy = bounds
        x_coords = np.arange(minx, maxx, cell_size)
        y_coords = np.arange(miny, maxy, cell_size)

        polygons = [
            Polygon([
                (x, y),
                (x + cell_size, y),
                (x + cell_size, y + cell_size),
                (x, y + cell_size),
            ])
            for x in x_coords
            for y in y_coords
        ]

        grid = gpd.GeoDataFrame({"geometry": polygons}, crs=self.metric_crs).to_crs(self.crs)
        grid["grid_id"] = range(len(grid))
        return grid

    def create_h3_dggs_grid(
        self,
        bounds_wgs84: Tuple[float, float, float, float] = (43.98, 9.50, 44.12, 9.60),
        resolution: int = 8,
    ) -> gpd.GeoDataFrame:
        """Generate an Uber H3 hexagonal Discrete Global Grid covering a WGS84 bounding box.

        Args:
            bounds_wgs84: (min_lon, min_lat, max_lon, max_lat) in EPSG:4326.
            resolution: H3 resolution (7 ≈ 5.16 km², 8 ≈ 0.74 km², 9 ≈ 0.11 km²).
        """
        min_lon, min_lat, max_lon, max_lat = bounds_wgs84
        bbox_poly = box(min_lon, min_lat, max_lon, max_lat)
        latlon_poly = h3.LatLngPoly([(lat, lon) for lon, lat in bbox_poly.exterior.coords])
        cells = sorted(h3.polygon_to_cells(latlon_poly, resolution))

        rows = []
        for cell in cells:
            # cell_to_boundary returns (lat, lon) tuples; Shapely Polygon takes (lon, lat)
            boundary_lonlat = [(lon, lat) for lat, lon in h3.cell_to_boundary(cell)]
            center_lat, center_lon = h3.cell_to_latlng(cell)
            rows.append({
                "h3_index": cell,
                "resolution": resolution,
                "center_lat": round(center_lat, 6),
                "center_lon": round(center_lon, 6),
                "area_km2": round(float(h3.cell_area(cell, unit="km^2")), 4),
                "geometry": Polygon(boundary_lonlat),
            })

        return gpd.GeoDataFrame(rows, crs=self.crs)

    def aggregate_to_h3(
        self,
        df: pd.DataFrame,
        resolution: int = 8,
        lat_col: str = "lat",
        lon_col: str = "lon",
        agg_cols: Optional[Iterable[str]] = None,
    ) -> gpd.GeoDataFrame:
        """Assign spatial observations to Uber H3 DGGS cells and compute zonal averages."""
        work = df.copy()
        work["h3_index"] = [
            h3.latlng_to_cell(float(lat), float(lon), resolution)
            for lat, lon in zip(work[lat_col], work[lon_col])
        ]

        if agg_cols is None:
            candidate_cols = ["delta_ndbi", "ndbi_2026", "ndvi_2026", "elevation_m", "slope_pct", "dist_to_laga", "flood_exposure_score"]
            agg_cols = [c for c in candidate_cols if c in work.columns]

        grouped = work.groupby("h3_index").agg(
            observation_count=("h3_index", "count"),
            **{f"mean_{col}": (col, "mean") for col in agg_cols},
        ).reset_index()

        geoms = []
        center_lats = []
        center_lons = []
        for cell in grouped["h3_index"]:
            geoms.append(Polygon([(lon, lat) for lat, lon in h3.cell_to_boundary(cell)]))
            clat, clon = h3.cell_to_latlng(cell)
            center_lats.append(round(clat, 6))
            center_lons.append(round(clon, 6))

        grouped["center_lat"] = center_lats
        grouped["center_lon"] = center_lons
        grouped["resolution"] = resolution
        return gpd.GeoDataFrame(grouped, geometry=geoms, crs=self.crs)

    def calculate_distance_to_features(
        self, grid: gpd.GeoDataFrame, features: gpd.GeoDataFrame, feature_name: str
    ) -> gpd.GeoDataFrame:
        """Calculate minimum metric distance (m) from each grid cell to the nearest feature."""
        grid_metric = grid.to_crs(self.metric_crs)
        features_metric = features.to_crs(self.metric_crs)
        grid[f"dist_to_{feature_name}"] = [
            float(features_metric.distance(row.geometry).min()) for _, row in grid_metric.iterrows()
        ]
        return grid

    def join_properties_to_grid(self, properties: pd.DataFrame, grid: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Join point observations to their containing grid polygon."""
        geometry = [Point(xy) for xy in zip(properties.longitude, properties.latitude)]
        gdf_props = gpd.GeoDataFrame(properties, crs=self.crs, geometry=geometry)
        return gpd.sjoin(gdf_props, grid, how="inner", predicate="within")


if __name__ == "__main__":
    joiner = SpatialJoiner()
    h3_grid = joiner.create_h3_dggs_grid(resolution=8)
    print(f"Generated {len(h3_grid)} Uber H3 Resolution-8 DGGS hexagons covering Hargeisa.")
