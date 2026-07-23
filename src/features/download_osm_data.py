import requests
import json
import os

def download_hargeisa_osm_data():
    # Bounding box for Hargeisa (South, West, North, East)
    # Latitude: ~9.50 to 9.60, Longitude: ~43.95 to 44.15
    bbox = "9.50,43.95,9.60,44.15"
    
    # Overpass API URL
    url = "https://overpass-api.de/api/interpreter"
    
    # Clean up and simplify the query to avoid large downloads that cause server rejections
    query = f"""[out:json][timeout:90];
(
  node["highway"="primary"]({bbox});
  way["highway"="primary"]({bbox});
  node["amenity"="school"]({bbox});
  node["amenity"="place_of_worship"]({bbox});
);
out body;
>;
out skel qt;"""
    
    headers = {
        'User-Agent': 'SahanAI-Hargeisa-Bot/1.0 (contact@sahanai-hargeisa.com)',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    print("Querying Overpass API for Hargeisa OSM data with headers...")
    response = requests.post(url, data={'data': query}, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        os.makedirs("data/raw", exist_ok=True)
        output_file = "data/raw/hargeisa_osm_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Success! Real-world Hargeisa OSM data saved to {output_file}")
    else:
        print(f"Error querying Overpass API: {response.status_code}")
        print(response.text[:500])

if __name__ == "__main__":
    download_hargeisa_osm_data()
