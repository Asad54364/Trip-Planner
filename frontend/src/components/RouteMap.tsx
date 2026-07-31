import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import type { Stop } from '../api/client'

interface Props {
  geometry: { type: string; coordinates: number[][] }
  stops: Stop[]
}

/* Custom colored markers */
function makeIcon(color: string, emoji: string): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:32px;height:32px;border-radius:50%;
      background:${color};
      display:flex;align-items:center;justify-content:center;
      font-size:16px;
      box-shadow:0 2px 8px rgba(0,0,0,0.4);
      border:2px solid white;
    ">${emoji}</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  })
}

const ICONS: Record<string, L.DivIcon> = {
  start: makeIcon('#22c55e', '📍'),
  pickup: makeIcon('#f97316', '📦'),
  dropoff: makeIcon('#ef4444', '🏁'),
  fuel: makeIcon('#eab308', '⛽'),
  break: makeIcon('#8b5cf6', '☕'),
  rest_10hr: makeIcon('#6366f1', '🛏️'),
  rest_34hr: makeIcon('#6366f1', '🛏️'),
  rest: makeIcon('#6366f1', '⏸️'),
}

/* Auto-fit bounds */
function FitBounds({ positions }: { positions: L.LatLngExpression[] }) {
  const map = useMap()
  const fitted = useRef(false)

  useEffect(() => {
    if (positions.length > 0 && !fitted.current) {
      const bounds = L.latLngBounds(positions as L.LatLngTuple[])
      map.fitBounds(bounds, { padding: [40, 40] })
      fitted.current = true
    }
  }, [positions, map])

  return null
}

export default function RouteMap({ geometry, stops }: Props) {
  // GeoJSON coords are [lng, lat] — Leaflet needs [lat, lng]
  const routePositions: [number, number][] =
    geometry?.coordinates?.map(([lng, lat]) => [lat, lng] as [number, number]) || []

  const stopPositions: [number, number][] =
    stops.map((s) => [s.lat, s.lng] as [number, number])

  const allPositions = [...routePositions, ...stopPositions]

  const center: [number, number] =
    allPositions.length > 0
      ? [
          allPositions.reduce((a, p) => a + p[0], 0) / allPositions.length,
          allPositions.reduce((a, p) => a + p[1], 0) / allPositions.length,
        ]
      : [39.8, -98.5] // Center of US

  return (
    <MapContainer
      center={center}
      zoom={6}
      style={{ height: '100%', width: '100%' }}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds positions={allPositions} />

      {/* Route polyline */}
      {routePositions.length > 0 && (
        <Polyline
          positions={routePositions}
          pathOptions={{
            color: '#3b82f6',
            weight: 4,
            opacity: 0.8,
            dashArray: undefined,
          }}
        />
      )}

      {/* Stop markers */}
      {stops.map((stop, idx) => (
        <Marker
          key={`${stop.type}-${idx}`}
          position={[stop.lat, stop.lng]}
          icon={ICONS[stop.type] || ICONS.rest}
        >
          <Popup>
            <div style={{ color: '#1e293b', fontFamily: 'Inter, sans-serif' }}>
              <strong style={{ fontSize: 14 }}>{stop.label}</strong>
              <br />
              <span style={{ fontSize: 12, color: '#64748b', textTransform: 'capitalize' }}>
                {stop.type.replace(/_/g, ' ')}
              </span>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
