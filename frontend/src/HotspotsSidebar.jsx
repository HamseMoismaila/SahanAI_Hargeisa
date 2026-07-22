import { useEffect, useState } from 'react';

export default function HotspotsSidebar({ onSelectHotspot }) {
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8080/api/hotspots')
      .then(res => res.json())
      .then(data => {
        if (data.features) {
          setHotspots(data.features);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const detailsMap = {
    "Jigjiga Yar (University District)": { zone: "Commercial/Residential", risk: "Low Risk", elevation: "1,290m", density: "High" },
    "Sha'ab (City Center)": { zone: "Government & Premium Retail", risk: "No Flood Risk", elevation: "1,270m", density: "Very High" },
    "Masalaha (South Airport Road)": { zone: "Light Industrial/Residential", risk: "Low Risk", elevation: "1,310m", density: "Medium" },
    "Ibrahim Koodbuur": { zone: "Residential Suburb", risk: "Medium Risk (near Laga)", elevation: "1,280m", density: "Medium-High" },
    "Hargeisa Club Area": { zone: "High-value Historical", risk: "Low Risk", elevation: "1,265m", density: "High" }
  };

  if (loading) return <div className="sidebar left-sidebar">Loading hotspots...</div>;

  return (
    <div className="sidebar left-sidebar">
      <h3>Top Investment Hotspots</h3>
      <p className="subtitle">Highest predicted growth areas in Hargeisa</p>
      
      <div className="hotspot-list">
        {hotspots.map((hs, idx) => {
          const name = hs.properties.name;
          const details = detailsMap[name] || { zone: "Mixed Use", risk: "Unknown", elevation: "N/A", density: "N/A" };
          const coords = hs.geometry.coordinates;

          return (
            <div key={idx} className="hotspot-card">
              <div className="hotspot-header">
                <h4>{name}</h4>
                <span className="growth-badge">{hs.properties.growth}</span>
              </div>
              <p className="reason">{hs.properties.reason}</p>
              
              <div className="hotspot-details-grid">
                <div><strong>Zone:</strong> {details.zone}</div>
                <div><strong>Risk:</strong> <span className={details.risk.includes("Medium") ? "risk-medium" : "risk-low"}>{details.risk}</span></div>
                <div><strong>Elev:</strong> {details.elevation}</div>
                <div><strong>Coords:</strong> {coords[1].toFixed(3)}, {coords[0].toFixed(3)}</div>
              </div>

              <button 
                className="locate-btn"
                onClick={() => onSelectHotspot([coords[1], coords[0]])}
              >
                Locate & Analyze
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
