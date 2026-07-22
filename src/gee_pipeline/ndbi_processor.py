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
            
        # Hargeisa Bounding Box roughly (closes properly with 5 coordinates)
        self.roi = ee.Geometry.Polygon(
            [[[43.90, 9.50], 
              [43.90, 9.60], 
              [44.10, 9.60], 
              [44.10, 9.50],
              [43.90, 9.50]]]
        )

    def calculate_ndbi(self, image, swir_band, nir_band):
        """
        Calculates the Normalized Difference Built-Up Index (NDBI).
        NDBI = (SWIR - NIR) / (SWIR + NIR)
        """
        ndbi = image.normalizedDifference([swir_band, nir_band]).rename('NDBI')
        return image.addBands(ndbi)

    def get_satellite_collection(self, year: int) -> ee.ImageCollection:
        """
        Fetches satellite imagery dynamically based on the year to support timeline checks:
        - 2015 to 2026: Sentinel-2 (B11 SWIR, B8 NIR)
        - 2013 to 2014: Landsat 8 (SR_B6 SWIR, SR_B5 NIR)
        - 1999 to 2012: Landsat 7 (SR_B5 SWIR, SR_B4 NIR)
        """
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        if year >= 2015:
            # Sentinel-2 Harmonized
            collection = (ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
                          .filterBounds(self.roi)
                          .filterDate(start_date, end_date)
                          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                          .map(lambda img: self.calculate_ndbi(img, 'B11', 'B8')))
        elif year >= 2013:
            # Landsat 8 Level 2 Surface Reflectance
            collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
                          .filterBounds(self.roi)
                          .filterDate(start_date, end_date)
                          .filter(ee.Filter.lt('CLOUD_COVER', 20))
                          .map(lambda img: self.calculate_ndbi(img, 'SR_B6', 'SR_B5')))
        else:
            # Landsat 7 Level 2 Surface Reflectance
            collection = (ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
                          .filterBounds(self.roi)
                          .filterDate(start_date, end_date)
                          .filter(ee.Filter.lt('CLOUD_COVER', 20))
                          .map(lambda img: self.calculate_ndbi(img, 'SR_B5', 'SR_B4')))
        return collection

    def get_ndbi_change(self, start_year: str, end_year: str) -> ee.Image:
        """
        Calculates the change in NDBI between two years to identify new construction.
        """
        img_start = self.get_satellite_collection(int(start_year)).median()
        img_end = self.get_satellite_collection(int(end_year)).median()
        
        ndbi_start = img_start.select('NDBI')
        ndbi_end = img_end.select('NDBI')
        
        return ndbi_end.subtract(ndbi_start).rename('NDBI_change')

    def get_ndbi_map_id(self, year: str) -> dict:
        """
        Generates an Earth Engine Map ID for the NDBI layer, suitable for rendering.
        """
        img = self.get_satellite_collection(int(year)).median()
        ndbi = img.select('NDBI')
        
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
            folder='SahanAI',
            scale=10,
            region=self.roi
        )
        task.start()
        print(f"Export task '{description}' started.")

if __name__ == "__main__":
    processor = NDBIProcessor()
    change_img = processor.get_ndbi_change("2020", "2024")
    print("NDBI change calculated successfully.")
