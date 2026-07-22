import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, useMap, useMapEvents } from 'react-leaflet';
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

// Click Event Handler
function MapClickHandler({ onClick }) {
  useMapEvents({
    click(e) {
      onClick(e.latlng);
    },
  });
  return null;
}

// Geoman Drawing Tool
function GeomanDrawControls({ onSelection }) {
  const map = useMap();

  useEffect(() => {
    map.pm.addControls({
      position: 'topright',
      drawCircle: false,
      drawMarker: false,
      drawCircleMarker: false,
      drawPolyline: false,
      drawText: false,
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
              const currentTotal = Math.round(sqmArea * data.current_price_sqm);
              const nextTotal = Math.round(sqmArea * data.next_year_price_sqm);
              
              const popupContent = `
                <div style="min-width: 180px; font-family: sans-serif; color: #1e293b;">
                  <h4 style="margin: 0 0 8px 0; color: #2563eb;">Plot Valuation</h4>
                  <p style="margin: 4px 0;"><strong>Total Area:</strong> ${Math.round(sqmArea).toLocaleString()} sqm</p>
                  <p style="margin: 4px 0;"><strong>Price per sqm:</strong> $${data.current_price_sqm}</p>
                  <hr style="margin: 8px 0; border: 0; border-top: 1px solid #e2e8f0;" />
                  <p style="margin: 4px 0;"><strong>Total Value Today:</strong> $${currentTotal.toLocaleString()}</p>
                  <p style="color: #10b981; margin: 4px 0; font-weight: bold;"><strong>Total Next Year:</strong> $${nextTotal.toLocaleString()}</p>
                  <p style="font-size: 0.85em; color: #64748b; margin: 4px 0;">Predicted Growth: +${data.growth_rate_pct}%</p>
                </div>
              `;
              layer.bindPopup(popupContent).openPopup();
              
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
        {/* Optimized Google Maps hybrid satellite/labels base layer */}
        <TileLayer
          attribution='&copy; Google Maps'
          url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
          maxNativeZoom={21}
          maxZoom={22}
          updateWhenZooming={false}
          updateWhenIdle={true}
          keepBuffer={8}
        />

        {ndbiTileUrl && (
          <TileLayer
            url={ndbiTileUrl}
            attribution="Map Data &copy; Google Earth Engine"
            opacity={0.6}
            maxZoom={22}
            updateWhenZooming={false}
            updateWhenIdle={true}
            keepBuffer={4}
          />
        )}

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
            pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.4, weight: 2 }}
          >
            <Popup>
              <div style={{ minWidth: '160px', color: '#1e293b' }}>
                <h4 style={{ margin: '0 0 5px 0', color: '#ef4444' }}>{feature.properties.name}</h4>
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
