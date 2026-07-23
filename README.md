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
* **Highway Proximity (Main Highway)**: Proximity to arterial transit corridors (e.g. Bypass, 150 Road, Taiwan Avenue) provides commercial value:
  $$\text{Road Premium} = 50 \cdot e^{-\frac{\text{Distance to Highway}}{1000\text{ meters}}}$$
* **Education Proximity (Schools)**: Proximity to major primary and international school clusters adds residential value:
  $$\text{School Premium} = 30 \cdot e^{-\frac{\text{Distance to Schools}}{1200\text{ meters}}}$$
* **Masjid Proximity (Community)**: Proximity to a neighborhood Masjid adds a premium for residential demand:
  $$\text{Masjid Premium} = 25 \cdot e^{-\frac{\text{Distance to Masjid}}{400\text{ meters}}}$$
* **Natural Hazard Proximity (Dooxa/Lagas)**: Real estate values are penalized by up to **30%** if the coordinates fall within `500 meters` of the winding dry riverbed (Dooxa Hargeisa) to account for seasonal flash flood vulnerabilities:
  $$\text{Penalty Multiplier} = 0.7 + 0.3 \cdot \left(\frac{\text{Distance to Dooxa}}{500}\right)$$

### 2. Localized Utility & Construction Surcharges
To provide Hargeisa developers with actionable analysis, the platform computes:
* **Water Supply Network (FAO SWALIM & HWA)**: Classifies plots based on Hargeisa Water Agency pipeline coverage. Plots within 2.5km of central trunks are labeled `Piped Municipal (HWA Network)` (low cost), while outlying zones default to `Private Water Truck Basin` (dependent on Booyad deliveries).
* **Access Road Classification**: Classifies connection access roads into `Paved Asphalt (Laami)`, `Graded Gravel (Carro-Cad)`, or `Unpaved Dirt Track` based on highway node proximity.
* **Topography & Foundation Cost Surcharge (NASA SRTM DEM)**: Estimates local slope gradients. Slopes $\ge$ 8.0% trigger a **+25% construction surcharge** (retaining walls required), while slopes 3.5% - 8.0% trigger a **+10% surcharge** (moderate grading required).
* **Excavation Soil Profile**: Classifies soil into `Hard Limestone Rock` (northern ridges requiring hydraulic jackhammer excavation), `Soft Sandy Soil` (dooxa margins), or `Clay & Silt Mix` (southern plains).

---

## Detailed Pricing Calculation & Prediction Logic

The platform calculates valuations and investment returns in three stages:

### Stage 1: Spatial Proximity & Pricing Engine (Backend)
When a coordinate is queried on the map, the backend ([train_model.py](file:///C:/Users/User/OneDrive%20-%20Nilai%20University/Desktop/goobta/src/models/train_model.py)) computes the Euclidean distance (converted to meters using the UTM scale factor) between the selected point and primary Hargeisa landmarks and infrastructure nodes.

$$\text{Current Price per sqm} = (\text{Base Price} + \text{University Premium} + \text{Road Premium} + \text{School Premium} + \text{Masjid Premium}) \times \text{Dooxa Penalty Multiplier}$$

### Stage 2: Compounding Appreciation Rate
The annual growth rate is dynamically simulated based on urban expansion corridors:
* Saturated central zones grow at a stable **5% to 8%** rate.
* Outlying development corridors (such as areas close to the university, bypass, and highway networks) receive development bonuses, compounding growth up to **15% to 25%** annually.

$$\text{Next Year Price} = \text{Current Price} \times (1 + \text{Appreciation Rate})$$

### Stage 3: Plot Scale & ROI Compounding (Frontend)
The React frontend ([EvaluationPanel.jsx](file:///C:/Users/User/OneDrive%20-%20Nilai%20University/Desktop/goobta/frontend/src/EvaluationPanel.jsx)) aggregates the base price per sqm relative to the chosen plot dimensions:
* **Per sqm Unit**: Area = $1\text{ sqm}$
* **Standard Small Plot**: Area = $18\text{m} \times 12\text{m} = 216\text{ sqm}$
* **Standard Large Plot**: Area = $24\text{m} \times 18\text{m} = 432\text{ sqm}$
* **Custom Plot**: Area = Custom drawn boundary polygon calculated via Turf.js (`@turf/area`).

The future value is compounded annually for the user-selected holding period ($n$ years):

$$\text{Future Value} = \text{Current Value} \times (1 + \text{Appreciation Rate})^n$$

---

## Map Layer Controls & Overlays
The Leaflet map cockpit integrates togglable layers via a Layer Control in the top-right corner:
1. **Google Satellite (Hybrid)**: Default high-resolution base imagery.
2. **HWA Water Pipelines**: Cites HWA & UN-Habitat pipeline mapping. Drawn as vibrant blue lines.
3. **Laga Flood Risk (Dooxa)**: Renders the central winding dry riverbed and draws parallel red boundary lines representing the 500-meter buffer zone boundaries flanking the Dooxa.
4. **Excavation Soil Zones**: Polygons outlining the Northern Limestone Bedrock (Hard Rock) and Southern Alluvial Clay Plains.

---

## Project Structure

```
sahan_ai/
├── data/                      # Raw, processed spatial data, and trained model files.
├── frontend/                  # React + Vite dashboard client.
│   ├── src/
│   │   ├── App.jsx            # Main cockpit entry layout.
│   │   ├── Map2D.jsx          # Leaflet map loaded with layers controls & measuring tools.
│   │   ├── HotspotsSidebar.jsx# List of ML-predicted high-growth zones (e.g. Mohamed Mooge).
│   │   ├── EvaluationPanel.jsx# ROI projection slider, side-by-side comparison, & sources.
│   │   ├── App.css            # Dark premium stylesheet (Inter font family).
│   │   └── main.jsx
│   └── package.json
├── src/
│   ├── api/
│   │   └── server.py          # FastAPI web server serving predictions and hotspots.
│   ├── gee_pipeline/
│   │   └── ndbi_processor.py  # Google Earth Engine satellite imagery processing.
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
1. **Interactive Navigation**: Drag and zoom on the Google Maps satellite interface. The map is locked focus to Hargeisa bounds.
2. **Instant Point Valuation**: Click any point on the map to query pricing, soil excavation types, slope, and water access feasibility.
3. **Compare Plots**: Select a plot and click **"+ Add to Compare List"** to save it. Select a second plot and add it to see side-by-side comparison stats (Value, ROI, Water, Road access, Soil, and Surcharges) in the right sidebar.
4. **Measure Distance**: Click the **"Measure Distance"** button in the bottom-left map corner. Click points on the map to draw a path and calculate geodesic distance. Click **"Reset"** to clear the path.
