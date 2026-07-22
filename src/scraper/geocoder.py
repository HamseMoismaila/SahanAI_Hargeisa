from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

class Geocoder:
    def __init__(self):
        user_agent = os.getenv("GEOCODING_USER_AGENT", "goobta_geocoder")
        self.geolocator = Nominatim(user_agent=user_agent)
        
    def get_coordinates(self, address_or_description: str):
        """
        Attempt to extract coordinates from a location string.
        For Hargeisa, locations might be neighborhoods (e.g., 'Jigjiga Yar', 'Sha'ab').
        """
        try:
            # Append Hargeisa, Somaliland to improve accuracy
            query = f"{address_or_description}, Hargeisa, Somaliland"
            location = self.geolocator.geocode(query, timeout=10)
            
            if location:
                return location.latitude, location.longitude
            return None, None
        except GeocoderTimedOut:
            print(f"Timeout geocoding: {address_or_description}")
            return None, None

    def geocode_dataframe(self, df: pd.DataFrame, address_column: str) -> pd.DataFrame:
        """
        Geocode a pandas DataFrame containing property listings.
        """
        print(f"Geocoding {len(df)} records...")
        
        lats = []
        lons = []
        
        for _, row in df.iterrows():
            address = row.get(address_column, '')
            lat, lon = self.get_coordinates(address)
            lats.append(lat)
            lons.append(lon)
            
        df['latitude'] = lats
        df['longitude'] = lons
        
        return df

if __name__ == "__main__":
    # Quick test
    geocoder = Geocoder()
    lat, lon = geocoder.get_coordinates("Jigjiga Yar")
    print(f"Coordinates for Jigjiga Yar: {lat}, {lon}")
