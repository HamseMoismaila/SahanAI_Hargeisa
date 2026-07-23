import requests
import json
import os

def download_hargeisa_elevation():
    # Grid of coordinates around Hargeisa (9x9 = 81 coordinates, under 100 limit)
    lats = [9.5 + (i * 0.012) for i in range(9)] 
    lons = [43.95 + (j * 0.024) for j in range(9)]
    
    lat_list = []
    lon_list = []
    for lat in lats:
        for lon in lons:
            lat_list.append(str(round(lat, 4)))
            lon_list.append(str(round(lon, 4)))
            
    lat_str = ",".join(lat_list)
    lon_str = ",".join(lon_list)
    
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lat_str}&longitude={lon_str}"
    
    print("Querying Open-Meteo API for Hargeisa elevation grid (81 points)...")
    headers = {'User-Agent': 'SahanAI-Hargeisa-Bot/1.0'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        os.makedirs("data/raw", exist_ok=True)
        output_file = "data/raw/hargeisa_elevation_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Success! Real-world elevation data saved to {output_file}")
    else:
        print(f"Error querying Open-Meteo API: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    download_hargeisa_elevation()
