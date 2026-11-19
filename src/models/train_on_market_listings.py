"""Train XGBoost Land Valuation & Environmental Risk Models on Real Satellite Features."""

import os
import joblib
import xgboost as xgb
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from src.features.feature_builder import build_real_spatial_dataframe

PRICE_FEATURES = [
    "ndbi_change",
    "dist_to_road",
    "dist_to_highway",
    "dist_to_center",
    "dist_to_university",
    "dist_to_laga",
    "dist_to_airport",
    "tax_rate",
    "population_density",
]


def train_and_test_market_model():
    df = build_real_spatial_dataframe()
    print(f"Loaded {len(df)} real-world geocoded records with Sentinel-2 & SRTM covariates.")

    X = df[PRICE_FEATURES]
    y = df["market_price_sqm"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=120,
        learning_rate=0.08,
        max_depth=4,
        random_state=42,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    rmse = float(mean_squared_error(y_test, preds) ** 0.5)
    r2 = float(r2_score(y_test, preds))

    print("\n--- MARKET VALUATION MODEL ACCURACY (REAL SENTINEL-2 + OSM + DOOXA FEATURES) ---")
    print(f"Testing RMSE: ${rmse:.2f}/sqm")
    print(f"Testing R2 Score: {r2:.4f}")
    for feat, imp in zip(PRICE_FEATURES, model.feature_importances_):
        print(f"  - {feat}: {imp * 100:.2f}%")

    os.makedirs("data/models", exist_ok=True)
    model_path = os.path.join("data/models", "xgboost_price_model.pkl")
    joblib.dump(model, model_path)
    print(f"\nSaved model to {model_path}")


if __name__ == "__main__":
    train_and_test_market_model()
