import json
import os
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error, r2_score

def extract_osm_landmarks():
    osm_path = "data/raw/hargeisa_osm_data.json"
    if not os.path.exists(osm_path):
        raise FileNotFoundError(f"Missing raw OSM data file: {osm_path}")
        
    with open(osm_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    elements = data.get("elements", [])
    node_coords = {el["id"]: (el["lat"], el["lon"]) for el in elements if el.get("type") == "node" and "lat" in el}
    
    roads = []
    schools = []
    masjids = []
    
    for el in elements:
        tags = el.get("tags", {})
        if el.get("type") == "node":
            lat = el.get("lat")
            lon = el.get("lon")
            if lat and lon:
                if tags.get("amenity") == "school":
                    schools.append((lat, lon))
                elif tags.get("amenity") == "place_of_worship":
                    masjids.append((lat, lon))
        elif el.get("type") == "way" and "highway" in tags:
            way_nodes = el.get("nodes", [])
            for node_id in way_nodes:
                if node_id in node_coords:
                    roads.append(node_coords[node_id])
                    
    return roads, schools, masjids

def calc_dist(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) * 111000

def perform_spatial_validation():
    listings_path = "data/raw/real_market_listings.csv"
    if not os.path.exists(listings_path):
        raise FileNotFoundError(f"Missing market listings file: {listings_path}")
        
    df_listings = pd.read_csv(listings_path)
    
    roads, schools, masjids = extract_osm_landmarks()
    city_center = (9.5600, 44.0650)
    university = (9.5400, 44.0200)
    laga_center = (9.5560, 44.0500)
    
    # 1. Feature Engineering
    records = []
    for _, row in df_listings.iterrows():
        pt = (row['lat'], row['lon'])
        dist_to_center = calc_dist(pt, city_center)
        dist_to_uni = calc_dist(pt, university)
        dist_to_road = min([calc_dist(pt, r) for r in roads]) if roads else 1000
        dist_to_school = min([calc_dist(pt, s) for s in schools]) if schools else 1500
        dist_to_masjid = min([calc_dist(pt, m) for m in masjids]) if masjids else 800
        dist_to_laga = calc_dist(pt, laga_center)
        
        ndbi_change = 0.15 * np.exp(-dist_to_center / 3000)
        
        records.append({
            'lat': row['lat'],
            'lon': row['lon'],
            'ndbi_change': ndbi_change,
            'dist_to_road': dist_to_road,
            'dist_to_highway': dist_to_road * 1.5,
            'dist_to_center': dist_to_center,
            'dist_to_university': dist_to_uni,
            'dist_to_laga': dist_to_laga,
            'market_price_sqm': row['market_price_sqm']
        })
        
    df = pd.DataFrame(records)
    
    features = [
        'ndbi_change', 
        'dist_to_road', 
        'dist_to_highway', 
        'dist_to_center', 
        'dist_to_university',
        'dist_to_laga'
    ]
    
    # 2. Spatial Split: Hargeisa is geographically divided North-South by the dry riverbed (Laga/Dooxa)
    # The riverbed lat is around 9.554 - 9.556
    split_lat = 9.554
    
    train_df = df[df['lat'] >= split_lat]  # North Hargeisa
    test_df = df[df['lat'] < split_lat]   # South Hargeisa
    
    print(f"Total listings available: {len(df)}")
    print(f"Staging Spatial Split: {len(train_df)} plots in North Hargeisa, {len(test_df)} plots in South Hargeisa.\n")
    
    X_train = train_df[features]
    y_train = train_df['market_price_sqm']
    
    X_test = test_df[features]
    y_test = test_df['market_price_sqm']
    
    # 3. Train Model on North Hargeisa
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=100,
        learning_rate=0.08,
        max_depth=4,
        random_state=42
    )
    
    print("Training XGBoost on NORTH HARGEISA vacant land data only...")
    model.fit(X_train, y_train)
    
    # 4. Predict on SOUTH HARGEISA (unseen geographical region)
    preds = model.predict(X_test)
    rmse = mean_squared_error(y_test, preds) ** 0.5
    r2 = r2_score(y_test, preds)
    
    print("\n--- SPATIAL CROSS-VALIDATION REPORT ---")
    print("Train Region: NORTH HARGEISA | Test Region: SOUTH HARGEISA")
    print(f"Testing RMSE on South Hargeisa: ${rmse:.2f}/sqm")
    print(f"Testing R2 Score on South Hargeisa: {r2:.6f}")
    
    # Analyze predictions
    test_results = pd.DataFrame({
        'Actual': y_test,
        'Predicted': preds,
        'Deviation': abs(y_test - preds)
    })
    print("\nSample Predictions on South Hargeisa plots:")
    print(test_results.head(10).to_string())

if __name__ == "__main__":
    perform_spatial_validation()
