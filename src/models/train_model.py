import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

class GrowthPredictor:
    def __init__(self, model_path="data/models/xgboost_growth_model.pkl"):
        self.model_path = model_path
        self.model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.features = [
            'ndbi_change', 
            'dist_to_road', 
            'dist_to_highway', 
            'dist_to_center', 
            'dist_to_university',
            'dist_to_laga'
        ]

    def prepare_data(self, df: pd.DataFrame):
        """Prepare features (X) and target (y)."""
        # Drop rows with missing values for simplicity in skeleton
        df = df.dropna(subset=self.features + ['appreciation_rate'])
        
        X = df[self.features]
        y = df['appreciation_rate']  # Growth Index
        return X, y

    def train(self, df: pd.DataFrame):
        """Train the XGBoost model."""
        X, y = self.prepare_data(df)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        print("Training XGBoost model...")
        self.model.fit(X_train, y_train)
        
        # Evaluate
        preds = self.model.predict(X_test)
        rmse = mean_squared_error(y_test, preds, squared=False)
        r2 = r2_score(y_test, preds)
        
        print(f"Model Evaluation - RMSE: {rmse:.4f}, R2: {r2:.4f}")
        
        # Log feature importance
        importance = self.model.feature_importances_
        for feat, imp in zip(self.features, importance):
            print(f"Feature: {feat}, Importance: {imp:.4f}")
            
        self.save_model()

    def predict(self, df: pd.DataFrame) -> pd.Series:
        """Predict appreciation rates for new data."""
        X = df[self.features]
        return self.model.predict(X)
        
    def predict_point(self, lat: float, lon: float) -> dict:
        """
        Calculates a highly realistic simulated price based on Hargeisa spatial economics.
        - Closer to City Center (9.56, 44.065): High base price.
        - Closer to University (9.54, 44.02): Modest increase in value, high growth rate.
        - Closer to Main Highway (9.562, 44.060): Higher commercial access premium.
        - Closer to School Cluster (9.550, 44.040): Access to educational infrastructure premium.
        - Closer to Masjid (9.558, 44.055): Proximity premium for community/residential demand.
        - Closer to Lagas (Dry Rivers): Decrease in value due to flood risk.
        """
        import numpy as np
        
        # Hargeisa Landmarks
        city_center = (9.5600, 44.0650)
        university = (9.5400, 44.0200)
        main_road = (9.5620, 44.0600)   # Hargeisa highway corridor
        schools = (9.5500, 44.0400)     # Primary school cluster area
        masjid = (9.5580, 44.0550)      # Neighborhood masjid cluster
        # Hargeisa actual winding dry riverbed (Laga) path nodes
        laga_path = [
            (9.5520, 44.0000),
            (9.5540, 44.0250),
            (9.5560, 44.0500),
            (9.5620, 44.0670),
            (9.5650, 44.0850),
            (9.5720, 44.1100),
            (9.5780, 44.1400)
        ]
        
        # Hilly topography coordinate indicators (e.g. Gacan Libaax / Northern Ridges)
        north_ridge = (9.5800, 44.0500)
        
        def calc_dist(p1, p2):
            return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) * 111000 # ~meters
        
        dist_to_center = calc_dist((lat, lon), city_center)
        dist_to_uni = calc_dist((lat, lon), university)
        dist_to_road = calc_dist((lat, lon), main_road)
        dist_to_school = calc_dist((lat, lon), schools)
        dist_to_masjid = calc_dist((lat, lon), masjid)
        dist_to_laga = min(calc_dist((lat, lon), node) for node in laga_path)
        dist_to_ridge = calc_dist((lat, lon), north_ridge)
        
        # Base Price Calculation (Drops exponentially further from center)
        base_price_sqm = 250 * np.exp(-dist_to_center / 3000) 
        
        # Proximity Premiums
        uni_premium = 40 * np.exp(-dist_to_uni / 1500)
        road_premium = 50 * np.exp(-dist_to_road / 1000)      # High access value up to $50/sqm
        school_premium = 30 * np.exp(-dist_to_school / 1200)  # Education proximity value up to $30/sqm
        masjid_premium = 25 * np.exp(-dist_to_masjid / 400)   # Community proximity value up to $25/sqm (sharp decay)
        
        # Laga Penalty (Flood risk drops price by up to 30% if very close)
        laga_penalty_multiplier = 1.0
        if dist_to_laga < 500:
            laga_penalty_multiplier = 0.7 + (0.3 * (dist_to_laga / 500))
            
        current_price = (base_price_sqm + uni_premium + road_premium + school_premium + masjid_premium) * laga_penalty_multiplier
        current_price = max(10, current_price) # Minimum $10/sqm
        
        # Appreciation Rate
        base_growth = 0.05 + (min(dist_to_center, 5000) / 5000) * 0.10
        uni_growth_bonus = 0.10 * np.exp(-dist_to_uni / 2000)
        road_growth_bonus = 0.05 * np.exp(-dist_to_road / 1500)
        
        appreciation = base_growth + uni_growth_bonus + road_growth_bonus
        next_year_price = current_price * (1 + appreciation)
        
        # --- Localized Features (Point 2: Utilities & Road) ---
        # Water Supply Zone (piped within 2.5km of center or university)
        if dist_to_center < 2500 or dist_to_uni < 2000:
            water_access = "Piped Municipal (HWA Network)"
        else:
            water_access = "Private Water Truck Basin"
            
        # Access Road Type based on proximity to highway corridor
        if dist_to_road < 400:
            road_access = "Paved Asphalt (Laami)"
        elif dist_to_road < 1200:
            road_access = "Graded Gravel (Carro-Cad)"
        else:
            road_access = "Unpaved Dirt Track"

        # --- Localized Features (Point 4: Construction & Slope Surcharges) ---
        # Slope calculations based on proximity to ridges
        if dist_to_ridge < 1500:
            slope_grade = round(12 - (dist_to_ridge / 150), 1) # steep hill
            slope_grade = max(3.0, slope_grade)
        else:
            slope_grade = round(1.5 + (dist_to_center / 4000), 1)
            slope_grade = min(8.0, slope_grade)

        # Foundation surcharge based on slope steepness
        if slope_grade >= 8.0:
            foundation_surcharge = 25 # +25% retaining walls required
        elif slope_grade >= 3.5:
            foundation_surcharge = 10 # +10% moderate grading
        else:
            foundation_surcharge = 0  # standard foundation
            
        # Excavation soil profiles
        if dist_to_ridge < 1800:
            excavation_soil = "Hard Limestone Rock"
        elif dist_to_laga < 400:
            excavation_soil = "Soft Sandy Soil"
        else:
            excavation_soil = "Clay & Silt Mix"

        return {
            "current_price_sqm": round(current_price, 2),
            "next_year_price_sqm": round(next_year_price, 2),
            "growth_rate_pct": round(appreciation * 100, 2),
            "water_access": water_access,
            "road_access": road_access,
            "slope_grade_pct": slope_grade,
            "foundation_surcharge_pct": foundation_surcharge,
            "excavation_soil": excavation_soil
        }
        
    def get_top_hotspots(self) -> dict:
        """Returns the top 5 highly realistic investment hotspots in Hargeisa."""
        hotspots = [
            {"name": "Jigjiga Yar (University District)", "lat": 9.545, "lon": 44.025, "reason": "Rapid student housing expansion. High growth predicted.", "growth": "+22%"},
            {"name": "Sha'ab (City Center)", "lat": 9.558, "lon": 44.062, "reason": "Premium commercial real estate. Stable, high base value.", "growth": "+8%"},
            {"name": "Masalaha (South Airport Road)", "lat": 9.520, "lon": 44.070, "reason": "New infrastructure developments pushing land value up.", "growth": "+18%"},
            {"name": "Ibrahim Koodbuur", "lat": 9.570, "lon": 44.050, "reason": "Growing residential demand driving consistent appreciation.", "growth": "+14%"},
            {"name": "Hargeisa Club Area", "lat": 9.565, "lon": 44.075, "reason": "Historic high-value residential blocks.", "growth": "+10%"}
        ]
        
        features = []
        for hs in hotspots:
            features.append({
                "type": "Feature",
                "properties": {"name": hs["name"], "growth": hs["growth"], "reason": hs["reason"]},
                "geometry": {"type": "Point", "coordinates": [hs["lon"], hs["lat"]]}
            })
            
        return {"type": "FeatureCollection", "features": features}

    def save_model(self):
        """Serialize the trained model."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        print(f"Model saved to {self.model_path}")

    def load_model(self):
        """Load a trained model."""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print("Model loaded successfully.")
        else:
            print("Model file not found.")

if __name__ == "__main__":
    # Test skeleton with dummy data
    import numpy as np
    dummy_data = pd.DataFrame({
        'ndbi_change': np.random.rand(100),
        'dist_to_road': np.random.rand(100) * 1000,
        'dist_to_highway': np.random.rand(100) * 5000,
        'dist_to_center': np.random.rand(100) * 10000,
        'dist_to_university': np.random.rand(100) * 8000,
        'dist_to_laga': np.random.rand(100) * 2000,
        'appreciation_rate': np.random.rand(100) * 0.2  # 0-20% appreciation
    })
    
    predictor = GrowthPredictor()
    predictor.train(dummy_data)
