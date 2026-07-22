import { useState, useEffect } from 'react';

export default function EvaluationPanel({ 
  selection, 
  prediction, 
  selectedArea, 
  comparisonList = [], 
  onAddToCompare, 
  onClearCompare 
}) {
  const [holdingYears, setHoldingYears] = useState(5);
  const [plotType, setPlotType] = useState('sqm'); // 'sqm', 'small', 'large'

  useEffect(() => {
    if (selectedArea) {
      setPlotType('custom');
    } else {
      setPlotType('sqm');
    }
  }, [selectedArea]);

  // Spatial Landmark Calculations helper
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

  const getProximityData = (lat, lng) => {
    const distToCenter = calcDist([lat, lng], cityCenter);
    const distToUni = calcDist([lat, lng], university);
    const distToRoad = calcDist([lat, lng], mainRoad);
    const distToSchool = calcDist([lat, lng], schools);
    const distToMasjid = calcDist([lat, lng], masjid);
    const distToLaga = calcDist([lat, lng], laga);
    return { distToCenter, distToUni, distToRoad, distToSchool, distToMasjid, distToLaga };
  };

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

  const handleCompareClick = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (!selection) return;
    onAddToCompare({
      lat: selection.lat,
      lng: selection.lng,
      area: activeArea,
      plotLabel: plotType === 'sqm' ? '1 sqm' : plotType === 'small' ? '18x12m Plot' : plotType === 'large' ? '24x18m Plot' : 'Custom Plot',
      currentPrice: currentPrice,
      totalValue: baseValue,
      growthRate: growthRate * 100,
      holdingYears: holdingYears,
      futureValue: futureValue,
      roi: totalRoi,
      proximity: getProximityData(selection.lat, selection.lng)
    });
  };

  const handleClearCompareClick = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    onClearCompare();
  };

  // Generate simple svg chart points for the trend
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
      {/* Comparison Drawer / Section if comparison list has items */}
      {comparisonList.length > 0 && (
        <div className="comparison-drawer-container">
          <div className="drawer-header">
            <h4>Plot Comparison ({comparisonList.length}/2)</h4>
            <button 
              type="button" 
              className="clear-compare-btn" 
              onClick={handleClearCompareClick}
            >
              Clear
            </button>
          </div>
          
          <div className="comparison-slots-layout">
            {comparisonList.map((item, idx) => (
              <div key={idx} className="comparison-card">
                <div className="comp-title">Plot {idx + 1} ({item.plotLabel})</div>
                <div className="comp-metric">Valuation: <strong>${item.totalValue.toLocaleString()}</strong></div>
                <div className="comp-metric">Growth: <strong className="text-success">+{item.growthRate.toFixed(1)}%</strong></div>
                <div className="comp-metric">ROI ({item.holdingYears} yr): <strong className="text-success">{item.roi}%</strong></div>
                <div className="comp-metric">Center: <strong>{(item.proximity.distToCenter / 1000).toFixed(2)} km</strong></div>
                <div className="comp-metric">Road: <strong>{(item.proximity.distToRoad / 1000).toFixed(2)} km</strong></div>
                <div className="comp-metric">Masjid: <strong>{item.proximity.distToMasjid} m</strong></div>
              </div>
            ))}
            
            {comparisonList.length === 1 && (
              <div className="comparison-card empty-card">
                <p>Select another area and click "Add to Compare" to see side-by-side stats</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Single Location Insights */}
      {!selection ? (
        <div className="empty-panel">
          <div className="empty-state-indicator">—</div>
          <h3>Property Insights</h3>
          <p className="subtitle">Select a hotspot, click on the map, or draw a boundary to view instant spatial analytics.</p>
        </div>
      ) : (
        <>
          <div className="evaluation-header-section">
            <h3>Investment Analytics</h3>
            <p className="subtitle">Automated spatial pricing & valuation insights</p>
            <button 
              type="button" 
              className="add-compare-btn" 
              onClick={handleCompareClick}
            >
              + Add to Compare List
            </button>
          </div>

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
                      type="button"
                      className={`selector-btn ${plotType === 'sqm' ? 'active' : ''}`}
                      onClick={(e) => { e.preventDefault(); setPlotType('sqm'); }}
                    >
                      Per sqm
                    </button>
                    <button 
                      type="button"
                      className={`selector-btn ${plotType === 'small' ? 'active' : ''}`}
                      onClick={(e) => { e.preventDefault(); setPlotType('small'); }}
                    >
                      Small Plot (18×12m)
                    </button>
                    <button 
                      type="button"
                      className={`selector-btn ${plotType === 'large' ? 'active' : ''}`}
                      onClick={(e) => { e.preventDefault(); setPlotType('large'); }}
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
                  <strong>{(getProximityData(selection.lat, selection.lng).distToCenter / 1000).toFixed(2)} km</strong>
                </li>
                <li>
                  <span>Proximity to Hargeisa Univ.</span>
                  <strong>{(getProximityData(selection.lat, selection.lng).distToUni / 1000).toFixed(2)} km</strong>
                </li>
                <li>
                  <span>Proximity to Main Highway</span>
                  <strong>{(getProximityData(selection.lat, selection.lng).distToRoad / 1000).toFixed(2)} km</strong>
                </li>
                <li>
                  <span>Proximity to Schools</span>
                  <strong>{(getProximityData(selection.lat, selection.lng).distToSchool / 1000).toFixed(2)} km</strong>
                </li>
                <li>
                  <span>Proximity to Masjid</span>
                  <strong>{getProximityData(selection.lat, selection.lng).distToMasjid} m</strong>
                </li>
                <li>
                  <span>Proximity to Laga (Riverbed)</span>
                  <strong className={getProximityData(selection.lat, selection.lng).distToLaga < 500 ? "text-danger" : ""}>
                    {getProximityData(selection.lat, selection.lng).distToLaga} m
                  </strong>
                </li>
                <li>
                  <span>Flood Vulnerability Risk</span>
                  <span className={`risk-badge ${getProximityData(selection.lat, selection.lng).distToLaga < 500 ? "risk-medium" : "risk-low"}`}>
                    {getProximityData(selection.lat, selection.lng).distToLaga < 500 ? "Moderate" : "Low Risk"}
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
        </>
      )}
    </div>
  );
}
