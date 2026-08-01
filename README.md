# Sahan AI: Spatial Intelligence & Real Estate Analytics Platform

Sahan AI is a geospatial intelligence platform that explores how satellite data, GIS analysis, and machine learning can support real estate analysis in Hargeisa, Somaliland.

The platform combines spatial data, infrastructure information, environmental factors, and machine learning techniques to generate estimated land value indicators, development insights, and investment analysis.

> [!NOTE]
> Rather than replacing professional property valuation, Sahan AI acts as a decision-support system for understanding how location, accessibility, environmental risks, and urban growth patterns influence real estate value.

---

## ⚠️ Problem Context

Real estate markets in emerging regions often face challenges such as:
* 📉 **Limited official property transaction datasets** (no centralized Multiple Listing Service)
* 📐 **Lack of standardized valuation systems**
* 🏗️ **Rapid, unmapped urban expansion**
* 🚧 **Incomplete infrastructure information**
* 💻 **Limited access to localized spatial analytics tools**

Hargeisa, Somaliland represents a unique case where property decisions are often based on local word-of-mouth knowledge rather than centralized data-driven systems. Sahan AI explores how modern geospatial technologies can help create more accessible, quantified real estate intelligence.

---

## 🛠️ Core Capabilities

### 1. Spatial Valuation Engine
The platform estimates land value indicators using location-based factors and accessibility metrics:
* **Location Accessibility Factors:**
  * Distance to Central Business District (CBD)
  * Distance to universities (Abaarso Tech, University of Hargeisa, Golis)
  * Distance to school clusters
  * Distance to community mosques
  * Distance to major roads and highways (Berbera Corridor, Bypass, 150 Road)

$$\text{Land Value Indicator} = \text{Base Location Value} + \text{Infrastructure Influence} + \text{Accessibility Premiums} - \text{Environmental Risk Factors}$$

The current pricing engine uses spatial rules and weighted factors to simulate how location characteristics influence land demand and value.

### 2. Environmental Risk Analysis
The system evaluates environmental conditions that may influence construction feasibility and land desirability:
* **Flood Risk:** Areas near seasonal waterways (*Dooxa/Lagas*) receive dynamic risk penalties based on proximity to safeguard investments against seasonal flash floods.
* **Terrain Analysis:** Digital Elevation Models (DEM) evaluate land slope:
  * **Low Slope ($< 3.5\%$):** Easier construction and foundation layout.
  * **Moderate Slope ($3.5\% - 8.0\%$):** Requires moderate grading/leveling.
  * **High Slope ($> 8.0\%$):** High construction complexity requiring retaining walls.
* **Soil Classification:** Categorizes terrain characteristics into Northern limestone bedrock (hard rock excavation), Southern alluvial clay plains, or Sandy dooxa margins.

### 3. Urban Growth Intelligence
Sahan AI uses satellite-derived spectral indicators to explore urban expansion patterns over time:
* **Satellite Analysis:** Tracks built-up area changes, construction activity trends, and development corridors.
* **Data Sources:** Sentinel-2 Surface Reflectance and Landsat-8 archives processed through the Google Earth Engine (GEE) API.
* **Urban Spectral Index (NDBI):**
  $$\text{NDBI} = \frac{\text{SWIR} - \text{NIR}}{\text{SWIR} + \text{NIR}}$$
  *(Where SWIR is Band 11 and NIR is Band 8 on Sentinel-2. Higher values indicate expanding built-up/concrete density over barren soil.)*

### 4. Infrastructure Accessibility Mapping
Integrates geographic infrastructure layers to calculate spatial accessibility variables:
* `distance_to_center` (meters to CBD)
* `distance_to_highway` (meters to paved roads)
* `distance_to_school` (meters to schools)
* `distance_to_water_network` (meters to HWA main municipal pipeline)

---

## 🤖 Machine Learning Pipeline

Sahan AI uses machine learning experiments to investigate relationships between spatial features and real estate growth patterns.

### Feature Engineering
Each location is transformed into a dataset containing:

| Feature | Description |
| :--- | :--- |
| **Distance to CBD** | Commercial accessibility and economic gravity |
| **Distance to roads** | Transportation access (asphalt vs. dirt) |
| **Distance to university** | Institutional demand influence |
| **Flood risk** | Environmental limitations (riverbed proximity) |
| **Slope** | Construction and foundation difficulty |
| **Soil characteristics** | Foundation development cost factors |
| **Satellite growth indicators** | Urban expansion signal ($\Delta$NDBI) |

### Model & Training
* **Model:** XGBoost Regressor combined with Scikit-learn preprocessing pipelines.
* **Prediction Target:** Forecasts spatial growth indices, opportunity scores, and estimated valuation patterns.

---

## 📊 Data Methodology & Sourcing

Because Somaliland does not currently have a centralized public property database, Sahan AI constructs its data pipeline from a combination of available sources:

### 1. Property Valuation Data
* **Sources:** Public property listings, online real estate advertisements, and community market postings.
* **Processing:** Cleaned for outliers, price normalized to USD (converting from SL Shillings), and geocoded via landmarks matching to assign coordinates.

### 2. Geospatial & Satellite Data
* **Sources:** OpenStreetMap (OSM) vector networks, GEE satellite imagery, and NASA Shuttle Radar Topography Mission (SRTM) DEM files.
* **Processing:** Collects spatial layers, converts vectors into coordinates, generates proximity metrics, and fits XGBoost models.

### ⚠️ Current Data Limitations
Sahan AI is currently a **research prototype** with the following limitations:
* Limited historical official sales transaction records.
* Property listing prices are not fully standardized.
* Some datasets are synthetic or estimated for testing model mechanics.
* Model predictions require further real-world validation.

---

## 🔬 Model Evaluation

Current prototype evaluation results:

| Metric | Result |
| :--- | :--- |
| **Model** | XGBoost Regressor |
| **RMSE** | 0.0663 |
| **R² Score** | -0.5185 |
| **Dataset** | Prototype spatial dataset |

> [!WARNING]
> These results should be interpreted carefully because the training dataset does not yet represent a complete real-world property market. The low $R^2$ indicates high variance due to sparse transaction records, which is a major driver for future real market dataset compilation.

---

## 🏛️ System Architecture

```text
                 +-------------------+
                 |       User        |
                 +-------------------+
                           |
                           v
                 +-------------------+
                 |  React Dashboard  |
                 +-------------------+
                           |
                           v
                 +-------------------+
                 |  FastAPI Backend  |
                 +-------------------+
                           |
            +--------------+--------------+
            |                             |
            v                             v
  +------------------+          +------------------+
  |  Spatial Engine  |          |   ML Pipeline    |
  | (GIS Processing) |          | (XGBoost Model)  |
  +------------------+          +------------------+
            |                             |
            +--------------+--------------+
                           |
                           v
           [Satellite + Infrastructure Data]
```

---

## 💻 Technology Stack

* **Frontend:** React, TypeScript, Vite, Tailwind CSS, Leaflet, CesiumJS / Resium
* **Backend:** FastAPI, Python, Pydantic, Uvicorn
* **Data Science:** XGBoost, Scikit-learn, Pandas, GeoPandas
* **Geospatial:** Google Earth Engine (GEE) API, OpenStreetMap (OSM), Turf.js, GDAL

---

## 🖥️ Dashboard Features

* **Interactive Map:** Explore Hargeisa bounds, view layers, and highlight high-growth corridors.
* **Property Analysis:** Select locations to evaluate, calculate water & slope surcharges, and run side-by-side plot comparisons.
* **Spatial Layer Controls:** Toggle overlays for satellite maps, flood risk zones, HWA water lines, and excavation soil zones.

---

## 📂 Project Structure

```text
sahan_ai/
├── data/
│   ├── models/              # Trained XGBoost models (.pkl)
│   └── raw/                 # Elevation JSON, OSM data, and market listings
├── frontend/
│   ├── src/
│   │   ├── Map2D.jsx        # Leaflet 2D spatial map
│   │   ├── Terrain3D.jsx    # CesiumJS 3D terrain viewer
│   │   ├── EvaluationPanel.jsx # ROI and valuation calculations panel
│   │   ├── HotspotsSidebar.jsx # Predicted growth hotspots sidebar
│   │   └── AIChat.jsx       # Real estate advisory AI chatbot
│   ├── package.json
│   └── vite.config.js
├── src/
│   ├── api/
│   │   └── server.py        # FastAPI server endpoints
│   ├── features/
│   │   ├── spatial_joiner.py # GeoPandas spatial coordinate aggregator
│   │   ├── hydrology.py      # Flash-flood proximity mapping
│   │   ├── download_elevation_data.py
│   │   └── download_osm_data.py
│   ├── gee_pipeline/
│   │   └── ndbi_processor.py # GEE Sentinel/Landsat processor
│   └── models/
│       ├── train_model.py    # Core training entry script
│       ├── spatial_validation.py
│       ├── train_on_market_listings.py
│       └── train_on_real_features.py
├── requirements.txt
└── README.md
```

---

## 🚀 Future Development

* **Real Market Dataset:** Partner with local banks/appraisers to compile verified land transactions and build a historical sales index database.
* **Advanced AI Models:** Experiment with Spatial Neural Networks (SNN), Graph Neural Networks (GNN) on road networks, and time-series forecasting.
* **Regional Expansion:** Extend the pipeline to other Somaliland cities (Berbera, Borama, Burao) and larger East African hubs.

---

## 📝 Disclaimer

Sahan AI provides experimental spatial estimates generated from available datasets and machine learning models. It is not an official property appraisal service and should not be used as the sole source for financial or investment decisions.

---

## 🚦 Project Status

🟡 **Research Prototype**

* **Implemented:**
  * ✅ Interactive GIS dashboard (React + Leaflet + CesiumJS)
  * ✅ Spatial analysis engine (`GeoPandas` + `shapely`)
  * ✅ Environmental risk layers (Flood, Slope, Soil type)
  * ✅ ML experimentation pipeline (XGBoost Regressor)
  * ✅ Location-based valuation indicators
* **Future Work:**
  * 🚧 Real transaction dataset collection
  * 🚧 Model validation & hyperparameter tuning
  * 🚧 Market expert and local appraiser collaboration
