import geopandas as gpd
from shapely.geometry import Point, Polygon
import pandas as pd
import numpy as np

class SpatialJoiner:
    def __init__(self, crs: str = "EPSG:4326"):
        """Initialize the spatial joiner with a specific Coordinate Reference System."""
        self.crs = crs
        # EPSG:32638 is UTM Zone 38N (good for Somaliland to calculate distances in meters)
        self.metric_crs = "EPSG:32638"

    def create_grid(self, bounds: tuple, cell_size: float = 500) -> gpd.GeoDataFrame:
        """
        Creates a spatial grid over a bounding box.
        cell_size is in meters if using a metric CRS.
        bounds = (minx, miny, maxx, maxy) in metric_crs
        """
        minx, miny, maxx, maxy = bounds
        
        # Create grid cells
        x_coords = np.arange(minx, maxx, cell_size)
        y_coords = np.arange(miny, maxy, cell_size)
        
        polygons = []
        for x in x_coords:
            for y in y_coords:
                polygons.append(Polygon([
                    (x, y),
                    (x + cell_size, y),
                    (x + cell_size, y + cell_size),
                    (x, y + cell_size)
                ]))
                
        grid = gpd.GeoDataFrame({'geometry': polygons}, crs=self.metric_crs)
        # Convert back to standard lat/lon for general use
        grid = grid.to_crs(self.crs)
        grid['grid_id'] = range(len(grid))
        
        return grid

    def calculate_distance_to_features(self, grid: gpd.GeoDataFrame, features: gpd.GeoDataFrame, feature_name: str) -> gpd.GeoDataFrame:
        """
        Calculates the minimum distance from each grid cell to the nearest feature (e.g., roads, airports).
        """
        # Convert to metric for accurate distance calculation
        grid_metric = grid.to_crs(self.metric_crs)
        features_metric = features.to_crs(self.metric_crs)
        
        # Get distances
        distances = []
        for idx, row in grid_metric.iterrows():
            dist = features_metric.distance(row.geometry).min()
            distances.append(dist)
            
        grid[f'dist_to_{feature_name}'] = distances
        return grid

    def join_properties_to_grid(self, properties: pd.DataFrame, grid: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Joins property listings with their corresponding grid cell.
        """
        # Convert properties to GeoDataFrame
        geometry = [Point(xy) for xy in zip(properties.longitude, properties.latitude)]
        gdf_props = gpd.GeoDataFrame(properties, crs=self.crs, geometry=geometry)
        
        # Spatial join
        joined = gpd.sjoin(gdf_props, grid, how="inner", predicate="within")
        
        return joined

if __name__ == "__main__":
    # Test initialization
    joiner = SpatialJoiner()
    print("SpatialJoiner initialized.")
    # Bounds roughly for Hargeisa in UTM Zone 38N
    # bounds = (xmin, ymin, xmax, ymax)
    # grid = joiner.create_grid(bounds, 500)
