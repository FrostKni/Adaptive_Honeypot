import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { memo, useEffect, useState, useMemo, useRef } from 'react'
import type { AttackLocation } from '../../types'

// Component to update map center dynamically
// Only updates when center actually changes and is valid
function MapCenterUpdater({ center }: { center: [number, number] }) {
  const map = useMap()
  const prevCenterRef = useRef<[number, number] | null>(null)
  
  useEffect(() => {
    // Only update if center is valid and has actually changed
    if (center[0] !== 0 || center[1] !== 0) {
      const prevCenter = prevCenterRef.current
      const hasChanged = !prevCenter || 
        prevCenter[0] !== center[0] || 
        prevCenter[1] !== center[1]
      
      if (hasChanged) {
        map.setView(center, map.getZoom())
        prevCenterRef.current = center
      }
    }
  }, [center, map])
  
  return null
}

interface AttackMapProps {
  attacks: AttackLocation[]
  onLocationClick?: (location: AttackLocation) => void
  refreshInterval?: number
}

// Theme colors matching the app's CSS variables
const THEME = {
  bgDeep: '#020204',
  bgBase: '#0a0a0f',
  bgElevated: '#12121a',
  accentPrimary: '#00d4ff',
  accentSuccess: '#10b981',
  accentDanger: '#ef4444',
  accentWarning: '#f59e0b',
  textPrimary: '#f1f5f9',
  textSecondary: '#94a3b8',
  borderGlow: 'rgba(0, 212, 255, 0.3)',
}

// Severity configuration - professional colors without harsh oranges
const severityConfig: Record<string, { 
  fill: string
  border: string
  glow: string
  label: string
}> = {
  low: { 
    fill: '#10b981',  // accentSuccess
    border: '#059669', 
    glow: 'rgba(16, 185, 129, 0.4)',
    label: 'LOW'
  },
  medium: { 
    fill: '#f59e0b',  // accentWarning
    border: '#d97706', 
    glow: 'rgba(245, 158, 11, 0.4)',
    label: 'MEDIUM'
  },
  high: { 
    fill: '#f97316', 
    border: '#ea580c', 
    glow: 'rgba(249, 115, 22, 0.5)',
    label: 'HIGH'
  },
  critical: { 
    fill: '#ef4444',  // accentDanger
    border: '#dc2626', 
    glow: 'rgba(239, 68, 68, 0.5)',
    label: 'CRITICAL'
  },
}

// Server location interface
interface ServerLocation {
  ip: string
  city: string
  country: string
  country_code: string
  region: string
  lat: number
  lng: number
  isp: string
  timezone: string
}

function AttackMapInner({ attacks, onLocationClick }: AttackMapProps) {
  const [isMounted, setIsMounted] = useState(false)
  const [serverLocation, setServerLocation] = useState<[number, number] | null>(null) // null until we have valid coordinates
  const [serverInfo, setServerInfo] = useState<ServerLocation | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    setIsMounted(true)
    
    // Fetch server location with auth token
    const fetchServerLocation = async () => {
      try {
        // Get auth token from localStorage
        const token = localStorage.getItem('token')
        if (!token) {
          console.warn('[AttackMap] No auth token found, using default location')
          setServerLocation([20, 0])
          setIsLoading(false)
          return
        }
        
        console.log('[AttackMap] Fetching server location with auth token...')
        
        const response = await fetch('/api/v1/analytics/server-location', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (response.ok) {
          const data: ServerLocation = await response.json()
          console.log('[AttackMap] Server location fetched successfully:', data.city, data.country, [data.lat, data.lng])
          setServerLocation([data.lat, data.lng])
          setServerInfo(data)
        } else {
          console.error('[AttackMap] Failed to fetch server location:', response.status, response.statusText)
          // Fallback to a reasonable default location
          setServerLocation([20, 0])
        }
      } catch (error) {
        console.error('[AttackMap] Failed to fetch server location:', error)
        // Fallback to a reasonable default location
        setServerLocation([20, 0])
      } finally {
        setIsLoading(false)
        console.log('[AttackMap] Loading complete, map will render')
      }
    }
    
    fetchServerLocation()
    
    return () => setIsMounted(false)
  }, [])

  const getMarkerRadius = (attackCount: number): number => {
    if (attackCount > 500) return 16
    if (attackCount > 100) return 13
    if (attackCount > 50) return 11
    if (attackCount > 10) return 9
    return 7
  }

  // Calculate statistics
  const stats = useMemo(() => {
    const total = attacks.reduce((sum, a) => sum + a.attack_count, 0)
    const topAttackers = [...attacks]
      .sort((a, b) => b.attack_count - a.attack_count)
      .slice(0, 3)
    return { total, topAttackers }
  }, [attacks])

  // Check if we have valid coordinates (not null and not [0, 0])
  const hasValidLocation = serverLocation !== null && 
    (serverLocation[0] !== 0 || serverLocation[1] !== 0)

  if (!isMounted || isLoading || !hasValidLocation) {
    return (
      <div 
        className="h-full w-full flex items-center justify-center"
        style={{ background: THEME.bgDeep }}
      >
        <div className="flex flex-col items-center gap-3">
          <div className="relative">
            <div 
              className="w-10 h-10 border-2 rounded-full"
              style={{ borderColor: 'rgba(0, 212, 255, 0.2)' }}
            />
            <div 
              className="absolute inset-0 w-10 h-10 border-2 rounded-full animate-spin"
              style={{ borderColor: `${THEME.accentPrimary} transparent transparent transparent` }}
            />
          </div>
          <span 
            className="text-sm font-mono"
            style={{ color: THEME.textSecondary }}
          >
            {isLoading ? 'DETECTING SERVER LOCATION...' : 'INITIALIZING THREAT MAP...'}
          </span>
        </div>
      </div>
    )
  }

  return (
    <div 
      className="h-full w-full relative"
      style={{ background: THEME.bgDeep }}
    >
      {/* Map Styling */}
      <style>{`
        /* Base map container */
        .leaflet-container {
          background: ${THEME.bgDeep} !important;
          font-family: 'JetBrains Mono', 'Fira Code', monospace;
        }
        
        /* Map tiles - minimal filtering */
        .leaflet-tile-pane {
          filter: brightness(0.85) !important;
        }
        
        .leaflet-tile {
          opacity: 1 !important;
        }
        
        /* Popup styling */
        .leaflet-popup-content-wrapper {
          background: linear-gradient(135deg, ${THEME.bgElevated} 0%, ${THEME.bgBase} 100%) !important;
          border: 1px solid ${THEME.borderGlow} !important;
          border-radius: 8px !important;
          box-shadow: 0 0 20px rgba(0, 212, 255, 0.15), 0 4px 12px rgba(0,0,0,0.5) !important;
        }
        
        .leaflet-popup-tip {
          background: ${THEME.bgElevated} !important;
        }
        
        .leaflet-popup-close-button {
          color: ${THEME.textSecondary} !important;
          font-size: 18px !important;
          padding: 6px 10px !important;
        }
        
        .leaflet-popup-close-button:hover {
          color: ${THEME.accentPrimary} !important;
        }
        
        .leaflet-popup-content {
          margin: 12px 16px !important;
          color: ${THEME.textPrimary} !important;
        }
        
        {/* Zoom controls - above status bar at bottom-right */}
        .leaflet-top.leaflet-left {
          top: auto !important;
          left: auto !important;
          right: 16px !important;
          bottom: 70px !important;
        }
        
        .leaflet-control-zoom {
          border: 1px solid ${THEME.borderGlow} !important;
          background: rgba(2, 2, 4, 0.95) !important;
          backdrop-filter: blur(8px) !important;
          border-radius: 8px !important;
          overflow: hidden !important;
          box-shadow: 0 0 15px rgba(0, 212, 255, 0.1) !important;
        }
        
        .leaflet-control-zoom a {
          background: transparent !important;
          color: ${THEME.accentPrimary} !important;
          border-bottom: 1px solid rgba(0, 212, 255, 0.15) !important;
          width: 36px !important;
          height: 36px !important;
          line-height: 36px !important;
          font-size: 16px !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
        }
        
        .leaflet-control-zoom a:hover {
          background: rgba(0, 212, 255, 0.1) !important;
        }
        
        .leaflet-control-zoom a:last-child {
          border-bottom: none !important;
        }
        
        /* Hide attribution */
        .leaflet-control-attribution {
          display: none !important;
        }
        
        /* Marker hover effect */
        .leaflet-interactive:hover {
          filter: brightness(1.2);
          cursor: pointer;
        }
      `}</style>

      <MapContainer
        center={serverLocation!}
        zoom={2}
        minZoom={2}
        maxZoom={16}
        className="h-full w-full"
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
        attributionControl={false}
        maxBounds={[[-85, -180], [85, 180]]}
        maxBoundsViscosity={0.8}
      >
        {/* Dark basemap */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          noWrap={true}
        />
        
        {/* Update map center when server location is fetched */}
        <MapCenterUpdater center={serverLocation!} />
        
        {/* Server/Honeypot marker - cyan pulsing dot */}
        <CircleMarker
          center={serverLocation!}
          radius={10}
          pathOptions={{
            fillColor: THEME.accentPrimary,
            color: '#0891b2',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9,
          }}
        >
          <Popup>
            <div className="min-w-[180px] p-3 font-mono">
              <div 
                className="font-bold text-sm mb-2"
                style={{ color: THEME.accentPrimary }}
              >
                HONEYPOT SERVER
              </div>
              <div style={{ color: THEME.textSecondary }}>
                <div className="flex justify-between">
                  <span>Status:</span>
                  <span style={{ color: THEME.accentSuccess }}>ONLINE</span>
                </div>
                <div className="flex justify-between">
                  <span>Mode:</span>
                  <span style={{ color: THEME.accentPrimary }}>ADAPTIVE</span>
                </div>
                {serverInfo && (
                  <>
                    <div className="flex justify-between mt-2 pt-2" style={{ borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                      <span>Location:</span>
                      <span style={{ color: THEME.textPrimary }}>{serverInfo.city}, {serverInfo.country}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>ISP:</span>
                      <span style={{ color: THEME.textPrimary }} className="truncate max-w-[100px]">{serverInfo.isp}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </Popup>
        </CircleMarker>

        {/* Attack markers - static, no roaming animation */}
        {attacks.map((location, index) => {
          const severity = location.severity || 'low'
          const config = severityConfig[severity]
          
          return (
            <CircleMarker
              key={`marker-${location.ip}-${index}`}
              center={[location.lat, location.lng]}
              radius={getMarkerRadius(location.attack_count)}
              pathOptions={{
                fillColor: config.fill,
                color: config.border,
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8,
              }}
              eventHandlers={{
                click: () => onLocationClick?.(location),
              }}
            >
              <Popup>
                <div className="min-w-[200px] p-3 font-mono">
                  {/* Header */}
                  <div 
                    className="flex items-center justify-between mb-3 pb-2"
                    style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}
                  >
                    <span 
                      className="font-bold text-sm"
                      style={{ color: THEME.accentPrimary }}
                    >
                      THREAT
                    </span>
                    <span 
                      className="px-2 py-0.5 rounded text-[10px] font-bold"
                      style={{ 
                        backgroundColor: config.glow,
                        color: config.fill,
                        border: `1px solid ${config.border}`
                      }}
                    >
                      {config.label}
                    </span>
                  </div>
                  
                  {/* IP */}
                  <div 
                    className="font-bold text-base mb-2"
                    style={{ color: THEME.textPrimary }}
                  >
                    {location.ip}
                  </div>
                  
                  {/* Details */}
                  <div 
                    className="space-y-1.5 text-xs"
                    style={{ color: THEME.textSecondary }}
                  >
                    <div className="flex items-center gap-2">
                      <svg className="w-3 h-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      </svg>
                      <span>{location.city ? `${location.city}, ` : ''}{location.country}</span>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <svg className="w-3 h-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <span style={{ color: THEME.textPrimary }} className="font-semibold">
                        {location.attack_count.toLocaleString()}
                      </span>
                      <span>attacks</span>
                    </div>
                    
                    {location.attack_types.length > 0 && (
                      <div 
                        className="flex flex-wrap gap-1 mt-2 pt-2"
                        style={{ borderTop: '1px solid rgba(255,255,255,0.1)' }}
                      >
                        {location.attack_types.slice(0, 3).map((type, i) => (
                          <span 
                            key={i}
                            className="px-1.5 py-0.5 rounded text-[10px]"
                            style={{ 
                              background: 'rgba(255,255,255,0.05)',
                              color: THEME.textSecondary
                            }}
                          >
                            {type}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>

      {/* ============ OVERLAY PANELS ============ */}

      {/* Active Threats - Top Left */}
      <div 
        className="absolute z-[500]"
        style={{ top: '16px', left: '16px' }}
      >
        <div 
          className="rounded-lg p-4 min-w-[140px]"
          style={{ 
            background: 'linear-gradient(135deg, rgba(18, 18, 26, 0.95), rgba(10, 10, 15, 0.95))',
            border: `1px solid ${THEME.borderGlow}`,
            boxShadow: '0 0 20px rgba(0, 212, 255, 0.1)',
            backdropFilter: 'blur(8px)'
          }}
        >
          <div 
            className="flex items-center gap-2 mb-3 pb-2"
            style={{ borderBottom: `1px solid rgba(0, 212, 255, 0.15)` }}
          >
            <div 
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: THEME.accentDanger }}
            />
            <span 
              className="text-[10px] font-semibold uppercase tracking-wider"
              style={{ color: THEME.accentPrimary }}
            >
              Active Threats
            </span>
          </div>
          
          <div 
            className="text-3xl font-bold font-mono leading-none mb-1"
            style={{ color: THEME.textPrimary }}
          >
            {attacks.length}
          </div>
          <div 
            className="text-xs"
            style={{ color: THEME.textSecondary }}
          >
            {stats.total.toLocaleString()} events
          </div>
        </div>
      </div>

      {/* Top Attackers - Top Right */}
      {stats.topAttackers.length > 0 && (
        <div 
          className="absolute z-[500]"
          style={{ top: '16px', right: '16px' }}
        >
          <div 
            className="rounded-lg p-4 min-w-[170px]"
            style={{ 
              background: 'linear-gradient(135deg, rgba(18, 18, 26, 0.95), rgba(10, 10, 15, 0.95))',
              border: `1px solid ${THEME.borderGlow}`,
              boxShadow: '0 0 20px rgba(0, 212, 255, 0.1)',
              backdropFilter: 'blur(8px)'
            }}
          >
            <div 
              className="flex items-center gap-2 mb-3 pb-2"
              style={{ borderBottom: `1px solid rgba(0, 212, 255, 0.15)` }}
            >
              <svg 
                className="w-3 h-3" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke={THEME.accentDanger}
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span 
                className="text-[10px] font-semibold uppercase tracking-wider"
                style={{ color: THEME.accentPrimary }}
              >
                Top Attackers
              </span>
            </div>
            
            <div className="space-y-2">
              {stats.topAttackers.map((a, idx) => (
                <div 
                  key={a.ip} 
                  className="flex items-center justify-between gap-3 p-2 rounded"
                  style={{ 
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.05)'
                  }}
                >
                  <div className="flex items-center gap-2">
                    <span 
                      className="text-[10px] font-bold"
                      style={{ color: THEME.accentPrimary }}
                    >
                      #{idx + 1}
                    </span>
                    <span 
                      className="text-xs font-mono truncate max-w-[80px]"
                      style={{ color: THEME.textPrimary }}
                    >
                      {a.ip}
                    </span>
                  </div>
                  <span 
                    className="text-xs font-bold"
                    style={{ color: THEME.accentDanger }}
                  >
                    {a.attack_count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Severity Legend - Bottom Left, above status bar */}
      <div 
        className="absolute z-[500]"
        style={{ bottom: '70px', left: '16px' }}
      >
        <div 
          className="rounded-lg p-3"
          style={{ 
            background: 'linear-gradient(135deg, rgba(18, 18, 26, 0.95), rgba(10, 10, 15, 0.95))',
            border: `1px solid ${THEME.borderGlow}`,
            boxShadow: '0 0 20px rgba(0, 212, 255, 0.1)',
            backdropFilter: 'blur(8px)'
          }}
        >
          <div 
            className="text-[10px] font-semibold uppercase tracking-wider mb-2"
            style={{ color: THEME.accentPrimary }}
          >
            Severity
          </div>
          
          <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
            {Object.entries(severityConfig).map(([level, config]) => (
              <div key={level} className="flex items-center gap-2">
                <div 
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ 
                    backgroundColor: config.fill,
                    boxShadow: `0 0 6px ${config.glow}`
                  }}
                />
                <span 
                  className="text-[10px] capitalize font-medium"
                  style={{ color: THEME.textSecondary }}
                >
                  {level}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Status Bar - Bottom Center */}
      <div 
        className="absolute z-[500] left-1/2 -translate-x-1/2"
        style={{ bottom: '24px' }}
      >
        <div 
          className="flex items-center gap-4 rounded-lg px-4 py-2"
          style={{ 
            background: 'linear-gradient(90deg, rgba(18, 18, 26, 0.9), rgba(10, 10, 15, 0.9), rgba(18, 18, 26, 0.9))',
            border: `1px solid rgba(0, 212, 255, 0.15)`,
            backdropFilter: 'blur(8px)'
          }}
        >
          <div className="flex items-center gap-2">
            <svg 
              className="w-3.5 h-3.5" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke={THEME.accentSuccess}
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span 
              className="text-[10px]"
              style={{ color: THEME.textSecondary }}
            >
              HONEYPOT:
            </span>
            <span 
              className="text-xs font-bold"
              style={{ color: THEME.accentSuccess }}
            >
              ONLINE
            </span>
          </div>
          
          <div 
            className="w-px h-4"
            style={{ background: 'rgba(255,255,255,0.1)' }}
          />
          
          <div className="flex items-center gap-2">
            <svg 
              className="w-3.5 h-3.5" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke={THEME.accentPrimary}
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <span 
              className="text-[10px]"
              style={{ color: THEME.textSecondary }}
            >
              MODE:
            </span>
            <span 
              className="text-xs font-bold"
              style={{ color: THEME.accentPrimary }}
            >
              ADAPTIVE
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

const AttackMap = memo(AttackMapInner)
export default AttackMap