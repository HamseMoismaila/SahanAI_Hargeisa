"""Unit and integration tests for Sahan AI geospatial, hydrology, H3 DGGS, and API modules."""

from src.api.server import app, get_h3_risk, get_hotspots, predict_location
from src.features.hydrology import HydrologyAnalyzer
from src.features.spatial_joiner import SpatialJoiner
from src.models.train_model import GrowthPredictor


def test_hydrology_dooxa_distance_and_exposure():
    hydro = HydrologyAnalyzer()
    # Point right on the Dooxa Hargeisa riverbed channel -> High Risk
    near_channel = hydro.compute_dooxa_exposure((9.5560, 44.0500), slope_pct=1.5)
    assert near_channel["dist_to_laga_m"] < 50.0
    assert near_channel["flood_risk_tier"] == "High"
    assert 0.65 <= near_channel["flood_exposure_score"] <= 1.0

    # Point far from the channel -> Low Risk
    far_point = hydro.compute_dooxa_exposure((9.5950, 44.0100), slope_pct=5.0)
    assert far_point["dist_to_laga_m"] > 1000.0
    assert far_point["flood_risk_tier"] == "Low"


def test_uber_h3_dggs_grid_and_aggregation():
    joiner = SpatialJoiner()
    grid = joiner.create_h3_dggs_grid(resolution=8)
    assert len(grid) > 100
    assert {"h3_index", "resolution", "area_km2", "geometry"}.issubset(grid.columns)
    assert all(grid["resolution"] == 8)


def test_growth_predictor_real_features_and_h3():
    predictor = GrowthPredictor()
    pred = predictor.predict_point(9.5600, 44.0650)
    assert pred["current_price_sqm"] >= 10.0
    assert "flood_exposure_score" in pred
    assert "dist_to_laga_m" in pred
    assert "delta_ndbi" in pred

    h3_geojson = predictor.get_h3_risk_hexagons(resolution=8)
    assert h3_geojson["type"] == "FeatureCollection"
    assert len(h3_geojson["features"]) > 0


def test_fastapi_route_handlers_and_registration():
    route_paths = {route.path for route in app.routes}
    assert {"/api/predict", "/api/hotspots", "/api/h3_risk", "/api/ndbi_tile"}.issubset(route_paths)

    pred = predict_location(lat=9.56, lon=44.065)
    assert "flood_risk_tier" in pred
    assert "slope_grade_pct" in pred

    hotspots = get_hotspots()
    assert hotspots["type"] == "FeatureCollection"

    h3_res = get_h3_risk(resolution=8)
    assert h3_res["type"] == "FeatureCollection"
    assert len(h3_res["features"]) == 39
