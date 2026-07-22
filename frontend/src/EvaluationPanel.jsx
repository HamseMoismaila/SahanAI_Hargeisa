import { useState, useEffect } from 'react';

export default function EvaluationPanel({ selection, prediction, selectedArea }) {
  const [holdingYears, setHoldingYears] = useState(5);
  const [plotType, setPlotType] = useState('sqm'); // 'sqm', 'small', 'large'

  useEffect(() => {
    if (selectedArea) {
      setPlotType('custom');
    } else {
      setPlotType('sqm');
    }
  }, [selectedArea]);

  if (!selection) {
    return (
      <div className="sidebar right-sidebar empty-panel">
        <div className="empty-state-indicator">—</div>
        <h3>Property Insights</h3>
        <p className="subtitle">Select a hotspot, click on the map, or draw a boundary to view instant spatial analytics.</p>
      </div>
    );
  }

  // Calculate simulated infrastructure distances based on coords
  const cityCenter = [9.5600, 44.0650];
  const university = [9.5400, 44.0200];
  const mainRoad = [9.5620, 44.0600];
  const schools = [9.5500, 44.0400];
  const masjid = [9.5580, 44.0550];
  const laga = [9.5550, 44.0700];

  const calcDist = (p1, p2) => {
    return Math.round(
      Math.sqrt(Math.pow(p1[0] - p2[0], 2) + Math.pow(p1[1] - p2[1], 2)) * 111000
    );
  };

  const distToCenter = calcDist([selection.lat, selection.lng], cityCenter);
  const distToUni = calcDist([selection.lat, selection.lng], university);
  const distToRoad = calcDist([selection.lat, selection.lng], mainRoad);
  const distToSchool = calcDist([selection.lat, selection.lng], schools);
  const distToMasjid = calcDist([selection.lat, selection.lng], masjid);
  const distToLaga = calcDist([selection.lat, selection.lng], laga);

  const SMALL_PLOT_SQM = 216; // 18m x 12m
  const LARGE_PLOT_SQM = 432; // 24m x 18m

  let activeArea = 1;
  let sizeLabel = "per sqm";

  if (selectedArea) {
    activeArea = selectedArea;
    sizeLabel = `${Math.round(selectedArea).toLocaleString()} sqm (Custom Plot)`;
  } else if (plotType === 'small') {
    activeArea = SMALL_PLOT_SQM;
    sizeLabel = "Standard Small Plot (18m × 12m = 216 sqm)";
  } else if (plotType === 'large') {
    activeArea = LARGE_PLOT_SQM;
    sizeLabel = "Standard Large Plot (24m × 18m = 432 sqm)";
  } else {
    activeArea = 1;
    sizeLabel = "1 sqm (Unit Price)";
  }

  const growthRate = prediction ? prediction.growth_rate_pct / 100 : 0.12;
  const currentPrice = prediction ? prediction.current_price_sqm : 85;
  
  const baseValue = Math.round(activeArea * currentPrice);
  const futureValue = Math.round(baseValue * Math.pow(1 + growthRate, holdingYears));
  const netGain = futureValue - baseValue;
  const totalRoi = Math.round((netGain / baseValue) * 100);

  const chartPoints = [];
  const chartHeight = 80;
  const chartWidth = 260;
  const years = Array.from({ length: 6 }, (_, i) => i);
  
  years.forEach((yr) => {
    const val = baseValue * Math.pow(1 + growthRate, yr);
    chartPoints.push(val);
  });

  const maxVal = Math.max(...chartPoints);
  const minVal = Math.min(...chartPoints);
  const valRange = maxVal - minVal || 1;

  const pointsString = chartPoints
    .map((val, idx) => {
      const x = (idx / 5) * chartWidth;
      const y = chartHeight - ((val - minVal) / valRange) * (chartHeight - 15) - 5;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div className="sidebar right-sidebar evaluation-panel">
      <h3>Investment Analytics</h3>
      <p className="subtitle">Automated spatial pricing & valuation insights</p>

      <div className="analytics-scroll-container">
        {/* Selected Coordinates / Area */}
        <div className="analytics-card">
          <div className="card-label">Selected Location</div>
          <div className="coords-display">
            {selection.lat.toFixed(6)}° N, {selection.lng.toFixed(6)}° E
          </div>
          
          {!selectedArea ? (
            <div className="plot-selector-group">
              <span className="selector-title">Select valuation unit:</span>
              <div className="selector-buttons">
                <button 
                  className={`selector-btn ${plotType === 'sqm' ? 'active' : ''}`}
                  onClick={() => setPlotType('sqm')}
                >
                  Per sqm
                </button>
                <button 
                  className={`selector-btn ${plotType === 'small' ? 'active' : ''}`}
                  onClick={() => setPlotType('small')}
                >
                  Small Plot (18×12m)
                </button>
                <button 
                  className={`selector-btn ${plotType === 'large' ? 'active' : ''}`}
                  onClick={() => setPlotType('large')}
                >
                  Large Plot (24×18m)
                </button>
              </div>
            </div>
          ) : (
            <div className="area-badge">
              Boundary Area: <strong>{Math.round(selectedArea).toLocaleString()} sqm</strong>
            </div>
          )}
        </div>

        {/* Pricing Metrics */}
        <div className="analytics-card highlight-card">
          <div className="card-label">Estimated Valuation</div>
          <div className="pricing-row">
            <div>
              <span className="price-label">Current Value</span>
              <div className="price-value">${baseValue.toLocaleString()}</div>
              <span className="unit-label-sub">{sizeLabel}</span>
            </div>
            <div>
              <span className="price-label">Growth Rate (pa)</span>
              <div className="price-growth">{prediction ? `+${prediction.growth_rate_pct}%` : 'Calculating...'}</div>
            </div>
          </div>
        </div>

        {/* Spatial Infrastructure Features */}
        <div className="analytics-card">
          <div className="card-label">Spatial Proximity</div>
          <ul className="proximity-list">
            <li>
              <span>Distance to Sha'ab (Center)</span>
              <strong>{(distToCenter / 1000).toFixed(2)} km</strong>
            </li>
            <li>
              <span>Proximity to Hargeisa Univ.</span>
              <strong>{(distToUni / 1000).toFixed(2)} km</strong>
            </li>
            <li>
              <span>Proximity to Main Highway</span>
              <strong>{(distToRoad / 1000).toFixed(2)} km</strong>
            </li>
            <li>
              <span>Proximity to Schools</span>
              <strong>{(distToSchool / 1000).toFixed(2)} km</strong>
            </li>
            <li>
              <span>Proximity to Masjid</span>
              <strong>{distToMasjid} m</strong>
            </li>
            <li>
              <span>Proximity to Laga (Riverbed)</span>
              <strong className={distToLaga < 500 ? "text-danger" : ""}>
                {distToLaga} m
              </strong>
            </li>
            <li>
              <span>Flood Vulnerability Risk</span>
              <span className={`risk-badge ${distToLaga < 500 ? "risk-medium" : "risk-low"}`}>
                {distToLaga < 500 ? "Moderate" : "Low Risk"}
              </span>
            </li>
          </ul>
        </div>

        {/* Interactive Growth Projection Slider */}
        <div className="analytics-card">
          <div className="card-label">Holding ROI Projection</div>
          <div className="holding-selector">
            <label>Hold Period: <strong>{holdingYears} Years</strong></label>
            <input 
              type="range" 
              min="1" 
              max="15" 
              value={holdingYears}
              onChange={(e) => setHoldingYears(parseInt(e.target.value))}
              className="roi-slider"
            />
          </div>
          
          <div className="projection-result">
            <div className="proj-row">
              <span>Value in Year {holdingYears}:</span>
              <strong>${futureValue.toLocaleString()}</strong>
            </div>
            <div className="proj-row text-success">
              <span>Estimated Return:</span>
              <strong>+${netGain.toLocaleString()} ({totalRoi}%)</strong>
            </div>
          </div>

          {/* Sparkline Graph */}
          <div className="sparkline-container">
            <svg width="100%" height="80" viewBox={`0 0 ${chartWidth} ${chartHeight}`}>
              <polyline
                fill="none"
                stroke="#3b82f6"
                strokeWidth="3"
                points={pointsString}
              />
              {chartPoints.map((val, idx) => {
                const x = (idx / 5) * chartWidth;
                const y = chartHeight - ((val - minVal) / valRange) * (chartHeight - 15) - 5;
                return (
                  <circle
                    key={idx}
                    cx={x}
                    cy={y}
                    r="4"
                    fill="#3b82f6"
                    className="chart-dot"
                  />
                );
              })}
            </svg>
            <div className="sparkline-labels">
              <span>Today</span>
              <span>Yr 5</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
