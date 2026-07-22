# Sahan AI: Spatial Intelligence Platform

Sahan AI is a spatial intelligence and machine learning platform designed to predict real estate growth hotspots and automate property land valuations in Hargeisa, Somaliland. 

The application integrates satellite imagery, geographic landmarks, and environmental risk layers to deliver instant spatial valuations and returns on investment (ROI).

---

## Technical Features

### 1. Spatial Valuation Model
The core pricing engine combines spatial metrics to dynamically estimate land value per square meter (sqm):
* **City Center Proximity (Sha'ab)**: Land values decay exponentially from the CBD (starting at `$250/sqm` base price):
  $$\text{Base Price} = 250 \cdot e^{-\frac{\text{Distance to Center}}{3000\text{ meters}}}$$
* **Institutional Premium (University)**: Locations near Hargeisa University gain an additional demand premium:
  $$\text{University Premium} = 40 \cdot e^{-\frac{\text{Distance to University}}{1500\text{ meters}}}$$
* **Highway Proximity (Main Highway)**: Proximity to arterial transit corridors provides commercial value:
  $$\text{Road Premium} = 50 \cdot e^{-\frac{\text{Distance to Highway}}{1000\text{ meters}}}$$
* **Education Proximity (Schools)**: Proximity to major primary and international school clusters adds residential value:
  $$\text{School Premium} = 30 \cdot e^{-\frac{\text{Distance to Schools}}{1200\text{ meters}}}$$
* **Masjid Proximity (Community)**: Proximity to a neighborhood Masjid adds a premium for residential demand:
  $$\text{Masjid Premium} = 25 \cdot e^{-\frac{\text{Distance to Masjid}}{400\text{ meters}}}$$
* **Natural Hazard Proximity (Lagas)**: Real estate values are penalized by up to **30%** if the coordinates fall within `500 meters` of a dry riverbed (Laga) to account for flash flood vulnerabilities:
  $$\text{Penalty Multiplier} = 0.7 + 0.3 \cdot \left(\frac{\text{Distance to Laga}}{500}\right)$$

### 2. Machine Learning Pipeline (XGBoost)
The backend leverages an XGBoost Regressor model (`xgb.XGBRegressor`) trained on structural spatial features:
1. `ndbi_change`: Normalized Difference Built-Up Index change over time (derived from Sentinel-2 satellite imagery) to index construction density.
2. `dist_to_road` / `dist_to_highway`: Proximity to arterial road networks.
3. `dist_to_center`: Distance to the city center.
4. `dist_to_university`: Distance to educational institutions.
5. `dist_to_laga`: Proximity to local hydrology streams.

---

## Detailed Pricing Calculation & Prediction Logic

The platform calculates valuations and investment returns in three stages:

### Stage 1: Spatial Proximity & Pricing Engine (Backend)
When a coordinate is queried on the map, the backend ([train_model.py](file:///C:/Users/User/OneDrive%20-%20Nilai%20University/Desktop/goobta/src/models/train_model.py)) computes the Euclidean distance (converted to meters using the UTM scale factor) between the selected point and primary Hargeisa landmarks:
* **Sha'ab (City Center)**: `(9.5600, 44.0650)`
* **Hargeisa University**: `(9.5400, 44.0200)`
* **Main Road (Highway)**: `(9.5620, 44.0600)`
* **School Cluster**: `(9.5500, 44.0400)`
* **Masjid Cluster**: `(9.5580, 44.0550)`
* **Major Laga (Dry River)**: `(9.5550, 44.0700)`

$$\text{Current Price per sqm} = (\text{Base Price} + \text{University Premium} + \text{Road Premium} + \text{School Premium} + \text{Masjid Premium}) \times \text{Laga Penalty Multiplier}$$

### Stage 2: Compounding Appreciation Rate
The annual growth rate is dynamically simulated based on urban expansion corridors:
* Saturated central zones grow at a stable **5% to 8%** rate.
* Outlying development corridors (such as areas close to the university and highway networks) receive development bonuses, compounding growth up to **15% to 25%** annually.

$$\text{Next Year Price} = \text{Current Price} \times (1 + \text{Appreciation Rate})$$

### Stage 3: Plot Scale & ROI Compounding (Frontend)
The React frontend ([EvaluationPanel.jsx](file:///C:/Users/User/OneDrive%20-%20Nilai%20University/Desktop/goobta/frontend/src/EvaluationPanel.jsx)) aggregates the base price per sqm relative to the chosen plot dimensions:
* **Per sqm Unit**: Area = $1\text{ sqm}$
* **Standard Small Plot**: Area = $18\text{m} \times 12\text{m} = 216\text{ sqm}$
* **Standard Large Plot**: Area = $24\text{m} \times 18\text{m} = 432\text{ sqm}$
* **Custom Plot**: Area = Custom drawn boundary polygon calculated via Turf.js (`@turf/area`).

The future value is compounded annually for the user-selected holding period ($n$ years):

$$\text{Future Value} = \text{Current Value} \times (1 + \text{Appreciation Rate})^n$$
$$\text{Estimated Return} = \text{Future Value} - \text{Current Value}$$
$$\text{Return on Investment (ROI \%)} = \left(\frac{\text{Estimated Return}}{\text{Current Value}}\right) \times 100$$

These compounding points are rendered in an inline SVG vector sparkline indicating the property valuation trend over the holding period.

---

## Project Structure

```
sahan_ai/
├── data/                      # Raw, processed spatial data, and trained model files.
├── frontend/                  # React + Vite dashboard client.
│   ├── src/
│   │   ├── App.jsx            # Main cockpit entry layout.
│   │   ├── Map2D.jsx          # Leaflet map loaded with Google Maps Hybrid layer.
│   │   ├── HotspotsSidebar.jsx# List of ML-predicted high-growth zones.
│   │   ├── EvaluationPanel.jsx# ROI projection slider, SVG trend lines, & proximity stats.
│   │   ├── App.css            # Dark premium stylesheet (Inter font family).
│   │   └── main.jsx
│   └── package.json
├── src/
│   ├── api/
│   │   └── server.py          # FastAPI web server serving predictions and hotspots.
│   ├── gee_pipeline/
│   │   └── ndbi_processor.py  # Google Earth Engine Sentinel-2 imagery processing.
│   ├── features/
│   │   ├── spatial_joiner.py  # GeoPandas metric coordinate conversions.
│   │   └── hydrology.py       # DEM-based flow routing and river proximity extractor.
│   └── models/
│       └── train_model.py     # XGBoost regressor modeling.
├── requirements.txt           # Python backend dependencies.
└── README.md                  # System instruction manual.
```

---

## Setup & Running Instructions

### 1. Backend Server Setup
Make sure you are in the project root directory, activate the Python virtual environment, and install dependencies:

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Run the FastAPI server
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8080
```

The API will now be running at `http://127.0.0.1:8080/`.

### 2. Frontend client Setup
Open a separate terminal window, navigate to the `frontend` folder, and run the developer server:

```bash
cd frontend

# Install node dependencies
npm install

# Start Vite server
npm run dev
```

Open [http://localhost:5173/](http://localhost:5173/) in your web browser to access the cockpit.

---

## How to Use the Dashboard
1. **Interactive Navigation**: Drag and zoom on the **Google Maps Satellite/Hybrid** interface. Standard labels are overlaid natively.
2. **Instant Point Valuation**: Click any point on the map to query the machine learning pricing model.
3. **Select Lot Dimensions**: Under *Selected Location* in the right panel, select **Per sqm**, **Small Plot (18m × 12m)**, or **Large Plot (24m × 18m)** to scale valuations.
4. **Draw Custom Boundaries**: Use the polygon/rectangle drawing toolbar on the top-right of the map to trace custom properties. It computes the total square meters and outputs the exact total plot evaluation.
5. **Simulate Growth Hold**: Move the *Hold Period* slider in the right panel to dynamically compound interest rates and simulate ROI holding graphs over 1-15 years.
