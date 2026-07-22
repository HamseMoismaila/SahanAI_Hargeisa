import ee

import os
from dotenv import load_dotenv

load_dotenv()

class NDBIProcessor:
    def __init__(self):
        """Initialize Google Earth Engine."""
        try:
            ee.Initialize()
            print("Google Earth Engine initialized successfully.")
        except ee.EEException:
            print("Earth Engine not authenticated. Please run 'earthengine authenticate'.")
            
        # Hargeisa Bounding Box roughly
        self.roi = ee.Geometry.Polygon(
            [[[43.90, 9.50], 
              [43.90, 9.60], 
              [44.10, 9.60], 
              [44.10, 9.50]]]
        )

    def calculate_ndbi(self, image):
        """
        Calculates the Normalized Difference Built-Up Index (NDBI).
        NDBI = (SWIR - NIR) / (SWIR + NIR)
        For Sentinel-2: SWIR is B11, NIR is B8
        """
        ndbi = image.normalizedDifference(['B11', 'B8']).rename('NDBI')
        return image.addBands(ndbi)

    def get_sentinel2_collection(self, start_date: str, end_date: str) -> ee.ImageCollection:
        """Fetch Sentinel-2 imagery for the ROI and date range."""
        collection = (ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
                      .filterBounds(self.roi)
                      .filterDate(start_date, end_date)
                      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                      .map(self.calculate_ndbi))
        return collection

    def get_ndbi_change(self, start_year: str, end_year: str) -> ee.Image:
        """
        Calculates the change in NDBI between two years to identify new construction.
        """
        img_start = self.get_sentinel2_collection(f"{start_year}-01-01", f"{start_year}-12-31").median()
        img_end = self.get_sentinel2_collection(f"{end_year}-01-01", f"{end_year}-12-31").median()
        
        ndbi_start = img_start.select('NDBI')
        ndbi_end = img_end.select('NDBI')
        
        # Calculate change
        ndbi_change = ndbi_end.subtract(ndbi_start).rename('NDBI_change')
        return ndbi_change

    def get_ndbi_map_id(self, year: str) -> dict:
        """
        Generates an Earth Engine Map ID for the NDBI layer, suitable for Folium rendering.
        """
        img = self.get_sentinel2_collection(f"{year}-01-01", f"{year}-12-31").median()
        ndbi = img.select('NDBI')
        
        # Visualization parameters: red means highly built-up
        vis_params = {
            'min': -0.5,
            'max': 0.3,
            'palette': ['blue', 'white', 'red']
        }
        
        return ndbi.getMapId(vis_params)

    def export_to_drive(self, image: ee.Image, description: str):
        """Export the resulting image to Google Drive."""
        task = ee.batch.Export.image.toDrive(
            image=image,
            description=description,
            folder='GoobtaAI',
            scale=10, # Sentinel-2 resolution
            region=self.roi
        )
        task.start()
        print(f"Export task '{description}' started.")

if __name__ == "__main__":
    # Test initialization and basic operations
    processor = NDBIProcessor()
    change_img = processor.get_ndbi_change("2020", "2024")
    # processor.export_to_drive(change_img, "Hargeisa_NDBI_Change_2020_2024")
    print("NDBI change calculated. Uncomment export to save.")
