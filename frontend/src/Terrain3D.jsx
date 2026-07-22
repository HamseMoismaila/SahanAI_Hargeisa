import { useEffect } from 'react';
import { Viewer, Cesium3DTileset, CameraFlyTo } from 'resium';
import { Cartesian3, Math as CesiumMath, Ion, EllipsoidTerrainProvider } from 'cesium';

// Note: To use Resium with Cesium, Vite requires some specific configuration for the Cesium static assets.
// For the sake of this skeleton, we assume the Cesium static files are handled or we use the direct CDN approach if needed.

export default function Terrain3D({ googleApiKey }) {
  useEffect(() => {
    // If we wanted to use Ion tokens, we set it here. We use Google API instead.
    Ion.defaultAccessToken = ''; 
  }, []);

  if (!googleApiKey) {
    return (
      <div style={{ height: '100%', minHeight: '400px', backgroundColor: '#1e293b', border: '1px dashed #475569', color: '#94a3b8', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', borderRadius: '8px', padding: '20px', textAlign: 'center' }}>
        <p style={{ margin: '0 0 10px 0', fontSize: '1.1rem', fontWeight: '600' }}>3D Terrain View Requires API Key</p>
        <p style={{ margin: 0, fontSize: '0.85rem', maxWidth: '350px' }}>Please add your GOOGLE_MAPS_API_KEY to the .env file and restart the server to stream 3D Photorealistic Tiles.</p>
      </div>
    );
  }

  const hargeisaCartesian = Cartesian3.fromDegrees(44.0650, 9.5600, 3000);

  return (
    <div style={{ height: '100%', width: '100%', borderRadius: '8px', overflow: 'hidden' }}>
      <Viewer 
        full 
        terrainProvider={new EllipsoidTerrainProvider()}
        imageryProvider={false}
        baseLayerPicker={false}
        geocoder={false}
        animation={false}
        timeline={false}
        infoBox={false}
      >
        <Cesium3DTileset 
          url={`https://tile.googleapis.com/v1/3dtiles/root.json?key=${googleApiKey}`} 
        />
        <CameraFlyTo 
          destination={hargeisaCartesian} 
          orientation={{
            heading: CesiumMath.toRadians(0.0),
            pitch: CesiumMath.toRadians(-45.0),
          }}
          duration={0} // Fly immediately
        />
      </Viewer>
    </div>
  );
}
