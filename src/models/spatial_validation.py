"""Spatial Group Cross-Validation & Uber H3 DGGS Evaluation for Sahan AI.

Evaluates model generalization across spatially disjoint Hargeisa districts
using real Sentinel-2 L2A (2020-2026) NDBI/NDVI reflectance, NASA SRTM elevation
and slope gradients, EPSG:32638 Dooxa riverbed distances, and OSM infrastructure.
"""

import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold

from src.features.feature_builder import build_real_spatial_dataframe
from src.features.spatial_joiner import SpatialJoiner

TRAIN_NEIGHBORHOODS = [
    "Jigjiga Yar, Hargeisa",
    "New Hargeisa, Hargeisa",
    "Dararweyne, Hargeisa",
]

TEST_NEIGHBORHOODS = [
    "Goljano, Hargeisa",
    "Ibrahim Koodbuur, Hargeisa",
    "Masalaha, Hargeisa",
]


def perform_spatial_validation() -> dict:
    """Run spatial block cross-validation across disjoint Hargeisa districts."""
    df = build_real_spatial_dataframe()

    env_features = [
        "ndbi_2020",
        "ndbi_change",
        "ndvi_2026",
        "elevation_m",
        "slope_pct",
        "dist_to_road",
        "dist_to_center",
        "dist_to_university",
        "dist_to_laga",
        "population_density",
    ]
    market_features = [
        "ndbi_change",
        "ndvi_2026",
        "elevation_m",
        "slope_pct",
        "dist_to_road",
        "dist_to_highway",
        "dist_to_center",
        "dist_to_university",
        "dist_to_laga",
        "dist_to_airport",
        "tax_rate",
        "population_density",
    ]

    # 1. 3-Fold Spatial GroupKFold across all 6 Hargeisa districts (prevents spatial leakage)
    gkf = GroupKFold(n_splits=3)
    oof_flood = np.zeros(len(df))
    oof_price = np.zeros(len(df))

    for tr_idx, te_idx in gkf.split(df, groups=df["neighborhood"]):
        tr, te = df.iloc[tr_idx], df.iloc[te_idx]

        fm = xgb.XGBRegressor(objective="reg:squarederror", n_estimators=120, learning_rate=0.06, max_depth=4, random_state=42)
        fm.fit(tr[env_features], tr["flood_exposure_score"])
        oof_flood[te_idx] = fm.predict(te[env_features])

        pm = xgb.XGBRegressor(objective="reg:squarederror", n_estimators=100, learning_rate=0.08, max_depth=4, random_state=42)
        pm.fit(tr[market_features], tr["market_price_sqm"])
        oof_price[te_idx] = pm.predict(te[market_features])

    flood_rmse = float(mean_squared_error(df["flood_exposure_score"], oof_flood) ** 0.5)
    flood_mae = float(mean_absolute_error(df["flood_exposure_score"], oof_flood))
    flood_r2 = float(r2_score(df["flood_exposure_score"], oof_flood))

    price_rmse = float(mean_squared_error(df["market_price_sqm"], oof_price) ** 0.5)
    price_r2 = float(r2_score(df["market_price_sqm"], oof_price))

    print(f"Total real-feature observations: {len(df)} across {df['neighborhood'].nunique()} districts")
    print("\n--- 3-FOLD SPATIAL GROUP CROSS-VALIDATION (UNSEEN DISTRICTS) ---")
    print(f"Flash-Flood Exposure RMSE: {flood_rmse:.4f} | MAE: {flood_mae:.4f} | R2: {flood_r2:.4f}")
    print(f"Informal Land Valuation RMSE: ${price_rmse:.2f}/sqm | R2: {price_r2:.4f}")

    # 2. Uber H3 DGGS Resolution-8 Zonal Aggregation
    joiner = SpatialJoiner()
    h3_gdf = joiner.aggregate_to_h3(
        df.rename(columns={"ndbi_change": "delta_ndbi"}),
        resolution=8,
        agg_cols=["delta_ndbi", "ndvi_2026", "elevation_m", "slope_pct", "dist_to_laga", "flood_exposure_score"],
    )
    print(f"\n--- UBER H3 DGGS (RES 8) ZONAL SUMMARY: {len(h3_gdf)} POPULATED HEXAGONS ---")
    print(
        h3_gdf[["h3_index", "observation_count", "mean_delta_ndbi", "mean_dist_to_laga", "mean_flood_exposure_score"]]
        .sort_values("mean_flood_exposure_score", ascending=False)
        .head(5)
        .to_string(index=False)
    )

    return {
        "flood_rmse": flood_rmse,
        "flood_mae": flood_mae,
        "flood_r2": flood_r2,
        "price_rmse": price_rmse,
        "price_r2": price_r2,
        "h3_cell_count": len(h3_gdf),
    }


if __name__ == "__main__":
    perform_spatial_validation()
