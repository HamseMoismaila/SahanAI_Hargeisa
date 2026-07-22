import React, { useState } from 'react';
import Map2D from './Map2D';
import HotspotsSidebar from './HotspotsSidebar';
import EvaluationPanel from './EvaluationPanel';
import './App.css';

const GOOGLE_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "";

function App() {
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [predictionData, setPredictionData] = useState(null);
  const [selectedArea, setSelectedArea] = useState(null);
  const [flyToCoords, setFlyToCoords] = useState(null);
  
  // State for side-by-side plot comparison
  const [comparisonList, setComparisonList] = useState([]);

  const handleSelectHotspot = (coords, name, info) => {
    setFlyToCoords(coords);
    setSelectedLocation({ lat: coords[0], lng: coords[1] });
    setSelectedArea(null);
    setPredictionData(null);
  };

  const handleMapSelection = (latlng, areaVal, prediction) => {
    setSelectedLocation(latlng);
    setSelectedArea(areaVal);
    setPredictionData(prediction);
  };

  const handleAddToCompare = (plotData) => {
    setComparisonList(prev => {
      if (prev.length >= 2) {
        // Shift out the older one to keep max 2
        return [prev[1], plotData];
      }
      return [...prev, plotData];
    });
  };

  const handleClearCompare = () => {
    setComparisonList([]);
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-brand">
          <h1>Sahan AI</h1>
          <span className="badge-beta">Spatial Intelligence</span>
        </div>
        <p className="header-tagline">Land valuation models and growth hotspot predictions in Hargeisa, Somaliland.</p>
      </header>
      
      <div className="dashboard-layout">
        {/* Left Sidebar */}
        <HotspotsSidebar onSelectHotspot={handleSelectHotspot} />

        {/* Center Main Content - Full Height Map */}
        <main className="dashboard-main full-map-layout">
          <section className="map-section">
            <Map2D 
              flyToCoords={flyToCoords} 
              clearFlyTo={() => setFlyToCoords(null)}
              onSelection={handleMapSelection}
              googleApiKey={GOOGLE_API_KEY}
            />
          </section>
        </main>

        {/* Right Sidebar - Analytics & Comparison Panel */}
        <EvaluationPanel 
          selection={selectedLocation} 
          prediction={predictionData} 
          selectedArea={selectedArea}
          comparisonList={comparisonList}
          onAddToCompare={handleAddToCompare}
          onClearCompare={handleClearCompare}
        />
      </div>
    </div>
  );
}

export default App;
