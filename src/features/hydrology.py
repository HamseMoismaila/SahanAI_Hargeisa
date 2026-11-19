"""Hydrological Flood-Exposure & Ephemeral Riverbed (Dooxa/Laga) Analyzer.

Supports both:
1. Raster-based D8 flow-direction and stream-network extraction via `pysheds`
   when a local SRTM GeoTIFF DEM is available (using `scipy.ndimage.distance_transform_edt`
   for pixel-level distance to extracted stream cells).
2. Metric vector distance (EPSG:32638, UTM Zone 38N) to the Maroodi Jeex /
   Dooxa Hargeisa seasonal riverbed channel geometry and SRTM slope hazard grading.
"""

from typing import Optional, Sequence, Tuple
import numpy as np
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.ops import transform as shapely_transform

# Maroodi Jeex / Dooxa Hargeisa seasonal riverbed centerline (lat, lon)
DOOXA_HARGEISA_LATLON: Tuple[Tuple[float, float], ...] = (
    (9.5520, 44.0000),
    (9.5540, 44.0250),
    (9.5560, 44.0500),
    (9.5620, 44.0670),
    (9.5650, 44.0850),
    (9.5720, 44.1100),
    (9.5780, 44.1400),
)


class HydrologyAnalyzer:
    """Computes D8 stream networks and metric flash-flood exposure along Hargeisa Dooxa channels."""

    def __init__(
        self,
        dem_path: Optional[str] = None,
        metric_crs: str = "EPSG:32638",
        channel_coords_latlon: Sequence[Tuple[float, float]] = DOOXA_HARGEISA_LATLON,
    ):
        self.dem_path = dem_path
        self.metric_crs = metric_crs
        self._to_metric = Transformer.from_crs("EPSG:4326", self.metric_crs, always_xy=True)

        # Shapely expects (lon, lat) when transforming from EPSG:4326 with always_xy=True
        channel_lonlat = LineString([(lon, lat) for lat, lon in channel_coords_latlon])
        self.channel_metric = shapely_transform(self._to_metric.transform, channel_lonlat)
        self._stream_dist_grid = None
        self._dem_grid = None

    def analyze_flood_risk(self, threshold: int = 1000):
        """Extract D8 stream network (Lagas) from a DEM raster using pysheds."""
        if not self.dem_path:
            return None
        from pysheds.grid import Grid
        from scipy.ndimage import distance_transform_edt

        try:
            grid = Grid.from_raster(self.dem_path)
            dem = grid.read_raster(self.dem_path)

            dem_filled = grid.fill_pits(dem)
            dem_resolved = grid.resolve_flats(dem_filled)
            fdir = grid.flowdir(dem_resolved)
            acc = grid.accumulation(fdir)
            streams = acc > threshold

            # Compute Euclidean pixel distance to nearest extracted stream cell (in meters)
            cell_dx, cell_dy = abs(grid.affine.a), abs(grid.affine.e)
            # If DEM is in geographic degrees (~9.55N), convert cell size to approximate meters
            if cell_dx < 1.0:
                cell_dx *= 111320.0 * np.cos(np.radians(9.55))
                cell_dy *= 110574.0
            self._stream_dist_grid = distance_transform_edt(~np.asarray(streams, dtype=bool), sampling=(cell_dy, cell_dx))
            self._dem_grid = grid
            return streams
        except FileNotFoundError:
            return None

    def calculate_distance_to_laga(self, point_coords: Tuple[float, float]) -> float:
        """Return metric distance (meters) from (lat, lon) to the nearest Dooxa/Laga channel."""
        lat, lon = float(point_coords[0]), float(point_coords[1])

        if self._stream_dist_grid is not None and self._dem_grid is not None:
            row, col = self._dem_grid.nearest_cell(lon, lat)
            if 0 <= row < self._stream_dist_grid.shape[0] and 0 <= col < self._stream_dist_grid.shape[1]:
                return float(self._stream_dist_grid[row, col])

        pt_metric = shapely_transform(self._to_metric.transform, Point(lon, lat))
        return float(self.channel_metric.distance(pt_metric))

    def compute_dooxa_exposure(
        self,
        point_coords: Tuple[float, float],
        slope_pct: float = 2.0,
    ) -> dict:
        """Compute composite flash-flood exposure index [0, 1] and tier from channel distance & slope."""
        dist_m = self.calculate_distance_to_laga(point_coords)

        # Lateral decay: maximum exposure within 150m of ephemeral Dooxa channel
        proximity_factor = float(np.exp(-dist_m / 400.0))
        # Flat/low-lying terrain (<3.5% slope) pools flash runoff; steep slopes (>8%) induce erosion
        lowland_factor = float(np.clip(1.0 - (slope_pct / 10.0), 0.25, 1.0))
        exposure_score = float(np.clip(0.75 * proximity_factor + 0.25 * proximity_factor * lowland_factor, 0.0, 1.0))

        if dist_m <= 150.0 or exposure_score >= 0.65:
            risk_tier = "High"
        elif dist_m <= 500.0 or exposure_score >= 0.30:
            risk_tier = "Moderate"
        else:
            risk_tier = "Low"

        return {
            "dist_to_laga_m": round(dist_m, 2),
            "slope_pct": round(float(slope_pct), 3),
            "flood_exposure_score": round(exposure_score, 4),
            "flood_risk_tier": risk_tier,
        }


if __name__ == "__main__":
    analyzer = HydrologyAnalyzer("data/raw/hargeisa_srtm_dem.tif")
    sample = analyzer.compute_dooxa_exposure((9.5600, 44.0650), slope_pct=1.8)
    print("Sample Dooxa exposure at city center:", sample)
