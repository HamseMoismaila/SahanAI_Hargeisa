import { useEffect, useState } from 'react';
import { 
  MapContainer, 
  TileLayer, 
  Marker, 
  Popup, 
  CircleMarker, 
  useMap, 
  useMapEvents,
  LayersControl,
  FeatureGroup,
  Polyline
} from 'react-leaflet';
import { GeoSearchControl, OpenStreetMapProvider, GoogleProvider } from 'leaflet-geosearch';
import { area } from '@turf/area';
import { polygon as turfPolygon } from '@turf/helpers';

import 'leaflet/dist/leaflet.css';
import 'leaflet-geosearch/dist/geosearch.css';
import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';
import L from 'leaflet';

// Fix for default Leaflet icon missing in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const HARGEISA_COORDS = [9.5600, 44.0650];

// HWA Water Pipelines Real-world transmission & distribution branches
const HWA_PIPELINES = [
  // Ged Deeble main transmission line (North to South)
  [[9.7000, 44.0500], [9.6500, 44.0520], [9.6000, 44.0580], [9.5600, 44.0650]],
  // Distribution Line 1 (Jigjiga Yar / Koodbur District)
  [[9.5600, 44.0650], [9.5750, 44.0300], [9.5850, 44.0200]],
  // Distribution Line 2 (Ga'an Libah)
  [[9.5600, 44.0650], [9.5500, 44.0800], [9.5450, 44.0950]],
  // Distribution Line 3 (Mohamoud Haybe)
  [[9.5600, 44.0650], [9.5400, 44.0500], [9.5350, 44.0350]]
];

// Laga river channels (Hydro-vulnerability zones)
const LAGA_CHANNELS = [
  // Main dry riverbed channel winding through Hargeisa center dividing the city north/south
  [[9.5450, 43.9900], [9.5480, 44.0200], [9.5520, 44.0400], [9.5550, 44.0550], [9.5600, 44.0680], [9.5650, 44.0850], [9.5680, 44.1000], [9.5780, 44.1300]]
];

// Search Component with Google Maps geocoding integration
function SearchField({ onLocationFound, googleApiKey }) {
  const map = useMap();

  useEffect(() => {
    // Dynamically choose Google Maps Provider if API key is present, fallback to OSM
    const provider = googleApiKey 
      ? new GoogleProvider({
          params: {
            key: googleApiKey,
            language: 'en',
            region: 'so'
          }
        })
      : new OpenStreetMapProvider({
          params: {
            'accept-language': 'en',
            countrycodes: 'so'
          }
        });

    const searchControl = new GeoSearchControl({
      provider: provider,
      style: 'bar',
      showMarker: false,
      autoClose: true,
      searchLabel: googleApiKey ? 'Search locations via Google Maps...' : 'Search Hargeisa locations...'
    });

    map.addControl(searchControl);

    const container = map.getContainer();
    const preventSubmit = (e) => {
      if (e.target && e.target.tagName === 'FORM' && e.target.closest('.leaflet-control-geosearch')) {
        e.preventDefault();
        e.stopPropagation();
      }
    };
    container.addEventListener('submit', preventSubmit);

    map.on('geosearch/showlocation', (result) => {
      onLocationFound({ lat: result.location.y, lng: result.location.x });
    });

    return () => {
      map.removeControl(searchControl);
      container.removeEventListener('submit', preventSubmit);
    };
  }, [map, onLocationFound, googleApiKey]);

  return null;
}

// Click Handler to capture selections
function MapClickHandler({ onClick }) {
  useMapEvents({
    click(e) {
      onClick(e.latlng);
    },
  });
  return null;
}

// Map Geoman Drawing Toolbar
function GeomanDrawControls({ onSelection }) {
  const map = useMap();

  useEffect(() => {
    map.pm.addControls({
      position: 'topright',
      drawMarker: false,
      drawCircleMarker: false,
      drawPolyline: false,
      drawCircle: false,
      drawPolygon: true,
      drawRectangle: true,
      editMode: true,
      dragMode: false,
      cutPolygon: false,
      removalMode: true,
    });

    map.on('pm:create', (e) => {
      const layer = e.layer;
      
      if (e.shape === 'Polygon' || e.shape === 'Rectangle') {
        const latlngs = layer.getLatLngs()[0];
        const coordinates = latlngs.map(ll => [ll.lng, ll.lat]);
        coordinates.push([latlngs[0].lng, latlngs[0].lat]);
        
        try {
          const poly = turfPolygon([coordinates]);
          const sqmArea = area(poly);
          const center = layer.getBounds().getCenter();
          
          fetch(`http://localhost:8080/api/predict?lat=${center.lat}&lon=${center.lng}`)
            .then(res => res.json())
            .then(data => {
              layer.bindPopup(`
                <div style="color: #1e293b;">
                  <h4 style="margin: 0 0 5px 0; color: #2563eb;">Custom Plot Area</h4>
                  <p style="margin: 4px 0;"><strong>Calculated Area:</strong> ${Math.round(sqmArea).toLocaleString()} sqm</p>
                  <p style="margin: 4px 0;"><strong>Unit Price:</strong> $${data.current_price_sqm}/sqm</p>
                  <p style="margin: 4px 0; font-weight: bold; color: #10b981;"><strong>Total Value:</strong> $${Math.round(sqmArea * data.current_price_sqm).toLocaleString()}</p>
                </div>
              `).openPopup();
              
              if (onSelection) {
                onSelection({ lat: center.lat, lng: center.lng }, sqmArea, data);
              }
            })
            .catch(err => console.error("Prediction error:", err));
        } catch (err) {
          console.error("Turf error:", err);
        }
      }
    });

    return () => {
      map.pm.removeControls();
      map.off('pm:create');
    };
  }, [map, onSelection]);

  return null;
}

// Fly Map to selected coords
function MapFlyTo({ coords, clearFlyTo, onSelection }) {
  const map = useMap();
  useEffect(() => {
    if (coords) {
      map.flyTo(coords, 18, { duration: 1.5 });
      clearFlyTo();
      
      fetch(`http://localhost:8080/api/predict?lat=${coords[0]}&lon=${coords[1]}`)
        .then(res => res.json())
        .then(data => {
          if (onSelection) {
            onSelection({ lat: coords[0], lng: coords[1] }, null, data);
          }
        })
        .catch(err => console.error(err));
    }
  }, [coords, map, clearFlyTo, onSelection]);
  return null;
}

export default function Map2D({ flyToCoords, clearFlyTo, onSelection, googleApiKey }) {
  const [ndbiTileUrl, setNdbiTileUrl] = useState('');
  const [hotspots, setHotspots] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [selectedYear, setSelectedYear] = useState(2026);

  useEffect(() => {
    // Only fetch hotspots list once on mount
    fetch('http://localhost:8080/api/hotspots')
      .then(res => res.json())
      .then(data => setHotspots(data))
      .catch(err => console.error(err));
  }, []);

  useEffect(() => {
    setNdbiTileUrl(''); // Reset tiles to display correct loading sequence
    fetch(`http://localhost:8080/api/ndbi_tile?year=${selectedYear}`)
      .then(res => res.json())
      .then(data => { if (data.tile_url) setNdbiTileUrl(data.tile_url); })
      .catch(err => console.error(err));
  }, [selectedYear]);

  useEffect(() => {
    if (!selectedLocation) return;
    setPrediction(null);
    
    fetch(`http://localhost:8080/api/predict?lat=${selectedLocation.lat}&lon=${selectedLocation.lng}`)
      .then(res => res.json())
      .then(data => {
        setPrediction(data);
        if (onSelection) {
          onSelection(selectedLocation, null, data);
        }
      })
      .catch(err => console.error(err));
  }, [selectedLocation]);

  return (
    <div className="map-container-wrapper">
      <div className="map-tooltip">
        Click anywhere to value, or draw a boundary using tools on the right.
      </div>

      <MapContainer 
        center={HARGEISA_COORDS} 
        zoom={13} 
        minZoom={11}
        maxZoom={22}
        style={{ height: '100%', width: '100%' }}
      >
        <LayersControl position="topright">
          {/* Base Layer */}
          <LayersControl.BaseLayer checked name="Google Satellite (Hybrid)">
            <TileLayer
              attribution='&copy; Google Maps'
              url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
              maxNativeZoom={21}
              maxZoom={22}
              updateWhenZooming={false}
              updateWhenIdle={true}
              keepBuffer={8}
            />
          </LayersControl.BaseLayer>

          {/* Overlays */}
          {ndbiTileUrl && (
            <LayersControl.Overlay name="Satellite Built-Up Density (NDBI)">
              <TileLayer
                url={ndbiTileUrl}
                attribution="Map Data &copy; Google Earth Engine"
                opacity={0.6}
                maxZoom={22}
                updateWhenZooming={false}
                updateWhenIdle={true}
                keepBuffer={4}
              />
            </LayersControl.Overlay>
          )}

          {/* Water Pipeline Overlay */}
          <LayersControl.Overlay checked name="HWA Water Pipelines">
            <FeatureGroup>
              {HWA_PIPELINES.map((line, idx) => (
                <Polyline 
                  key={idx} 
                  positions={line} 
                  pathOptions={{ color: '#0284c7', weight: 4, opacity: 0.85 }} 
                >
                  <Popup>
                    <div style={{ color: '#1e293b' }}>
                      <strong>Hargeisa Water Agency Pipeline</strong>
                      <p style={{ margin: '4px 0', fontSize: '0.85em' }}>Geed Deeble Aquifer Transmission Spine</p>
                    </div>
                  </Popup>
                </Polyline>
              ))}
            </FeatureGroup>
          </LayersControl.Overlay>

          {/* Laga Flood Risk Channels Overlay */}
          <LayersControl.Overlay checked name="Laga Flood Risk Channels">
            <FeatureGroup>
              {LAGA_CHANNELS.map((line, idx) => (
                <Polyline 
                  key={idx} 
                  positions={line} 
                  pathOptions={{ color: '#ef4444', weight: 5, opacity: 0.65, dashArray: '10, 10' }} 
                >
                  <Popup>
                    <div style={{ color: '#1e293b' }}>
                      <strong>Active Laga (Dry Riverbed)</strong>
                      <p style={{ margin: '4px 0', fontSize: '0.85em', color: '#b91c1c' }}>High Flash-Flood Risk Area (500m Buffer Penalty)</p>
                    </div>
                  </Popup>
                </Polyline>
              ))}
            </FeatureGroup>
          </LayersControl.Overlay>
        </LayersControl>

        <SearchField onLocationFound={(loc) => setSelectedLocation(loc)} googleApiKey={googleApiKey} />
        <MapClickHandler onClick={(loc) => setSelectedLocation(loc)} />
        <GeomanDrawControls onSelection={onSelection} />
        <MapFlyTo coords={flyToCoords} clearFlyTo={clearFlyTo} onSelection={onSelection} />

        {selectedLocation && (
          <Marker position={selectedLocation}>
            <Popup>
              <div style={{ minWidth: '150px', color: '#1e293b' }}>
                <h4 style={{ margin: '0 0 5px 0', color: '#2563eb' }}>Point Valuation</h4>
                {prediction ? (
                  <>
                    <p style={{ margin: '4px 0' }}><strong>Current Price:</strong> ${prediction.current_price_sqm}/sqm</p>
                    <p style={{ color: '#10b981', margin: '4px 0', fontWeight: 'bold' }}>
                      <strong>Next Year:</strong> ${prediction.next_year_price_sqm}/sqm
                    </p>
                    <p style={{ margin: '4px 0' }}><strong>Predicted Growth:</strong> +{prediction.growth_rate_pct}%</p>
                  </>
                ) : (
                  <p>Calculating ML Prediction...</p>
                )}
              </div>
            </Popup>
          </Marker>
        )}

        {hotspots && hotspots.features.map((feature, idx) => (
          <CircleMarker 
            key={idx}
            center={[feature.geometry.coordinates[1], feature.geometry.coordinates[0]]}
            radius={18}
            pathOptions={{ color: '#e11d48', fillColor: '#e11d48', fillOpacity: 0.35, weight: 2 }}
          >
            <Popup>
              <div style={{ minWidth: '160px', color: '#1e293b' }}>
                <h4 style={{ margin: '0 0 5px 0', color: '#e11d48' }}>{feature.properties.name}</h4>
                <p style={{ margin: '4px 0' }}><strong>Growth Rank:</strong> <span style={{ color: '#10b981', fontWeight: 'bold' }}>{feature.properties.growth}</span></p>
                <p style={{ margin: 0, fontSize: '0.85em', color: '#4b5563' }}>{feature.properties.reason}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
