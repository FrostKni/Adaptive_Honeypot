import { Activity, Server, AlertTriangle, TrendingUp, TrendingDown, Shield, Zap, Globe } from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'
import { useDashboardStats } from '../hooks/useApi'
import { useState, useEffect } from 'react'
import AttackMap from '../components/Dashboard/AttackMap'
import type { AttackLocation } from '../types'

interface Stats {
  total_attacks: number
  active_honeypots: number
  active_sessions: number
  attacks_today: number
  attacks_by_type: Record<string, number>
  attacks_by_severity: Record<string, number>
  top_attackers: Array<{ ip: string; count: number }>
  attack_timeline: Array<{ time: string; count: number }>
  honeypot_health: Array<{ id: string; name: string; health: number }>
}

export default function Dashboard() {
  const { lastMessage } = useWebSocket()
  const [realtimeStats, setRealtimeStats] = useState<Stats | null>(null)
  const [attackLocations, setAttackLocations] = useState<AttackLocation[]>([])
  const [mapLoading, setMapLoading] = useState(true)

  const { data: stats, isLoading } = useDashboardStats()

  useEffect(() => {
    const msg = lastMessage as { type?: string; data?: Stats } | null
    if (msg?.type === 'status_update') {
      setRealtimeStats(msg.data ?? null)
    }
  }, [lastMessage])

  // Fetch attack locations
  useEffect(() => {
    const fetchAttackLocations = async () => {
      try {
        const token = localStorage.getItem('token')
        const response = await fetch('/api/v1/analytics/attack-locations?hours=24&limit=100', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })
        if (response.ok) {
          const data = await response.json()
          setAttackLocations(data)
        }
      } catch (error) {
        console.error('Failed to fetch attack locations:', error)
      } finally {
        setMapLoading(false)
      }
    }

    fetchAttackLocations()
    // Refresh every 30 seconds
    const interval = setInterval(fetchAttackLocations, 30000)
    return () => clearInterval(interval)
  }, [])

  const displayStats = realtimeStats || stats

  const statCards = [
    { 
      name: 'Active Honeypots', 
      value: displayStats?.active_honeypots ?? 0, 
      icon: Server, 
      color: 'cyan',
      trend: 'Monitoring',
      trendUp: true
    },
    { 
      name: 'Total Attacks', 
      value: displayStats?.total_attacks ?? 0, 
      icon: AlertTriangle, 
      color: 'red',
      trend: 'All time',
      trendUp: false
    },
    { 
      name: 'Attacks Today', 
      value: displayStats?.attacks_today ?? 0, 
      icon: Activity, 
      color: 'purple',
      trend: 'Last 24h',
      trendUp: true
    },
    { 
      name: 'Active Sessions', 
      value: displayStats?.active_sessions ?? 0, 
      icon: Zap, 
      color: 'green',
      trend: 'Live',
      trendUp: true
    },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-dark-800 rounded-full"></div>
            <div className="absolute top-0 left-0 w-16 h-16 border-4 border-cyber-500 rounded-full border-t-transparent animate-spin"></div>
          </div>
          <p className="text-slate-500">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, index) => {
          const Icon = stat.icon
          return (
            <div 
              key={stat.name}
              className="stat-card group"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`stat-icon stat-icon-${stat.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
                <span className={`flex items-center gap-1 text-xs font-medium ${stat.trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
                  {stat.trendUp ? (
                    <TrendingUp className="w-3.5 h-3.5" />
                  ) : (
                    <TrendingDown className="w-3.5 h-3.5" />
                  )}
                  {stat.trend}
                </span>
              </div>
              <div>
                <p className="stat-value">{stat.value.toLocaleString()}</p>
                <p className="text-sm text-slate-400 mt-1">{stat.name}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Global Threat Map */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl border border-cyan-500/20 overflow-hidden shadow-[0_0_30px_rgba(34,211,238,0.1)]">
        {/* Map Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-cyan-500/20 bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
              <Globe className="w-4 h-4 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Global Threat Map</h3>
              <p className="text-xs text-slate-400">Real-time attack visualization</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-full">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              <span className="text-xs text-green-400 font-medium">LIVE</span>
            </div>
          </div>
        </div>
        
        {/* Map Container */}
        <div className="h-[600px] relative">
          {mapLoading ? (
            <div className="flex items-center justify-center h-full bg-[#0a0f1a]">
              <div className="flex flex-col items-center gap-4">
                <div className="relative">
                  <div className="w-14 h-14 border-2 border-cyan-500/30 rounded-full" />
                  <div className="absolute inset-0 w-14 h-14 border-2 border-t-cyan-500 rounded-full animate-spin" />
                </div>
                <div className="text-center">
                  <p className="text-cyan-400 text-sm font-mono">Loading threat data...</p>
                  <p className="text-slate-500 text-xs mt-1">Initializing security map</p>
                </div>
              </div>
            </div>
          ) : (
            <AttackMap 
              key="attack-map"
              attacks={attackLocations} 
              refreshInterval={30000}
            />
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Zap className="w-5 h-5 text-cyber-500" />
            Quick Actions
          </h3>
        </div>
        <div className="flex flex-wrap gap-3">
          <a 
            href="/honeypots" 
            className="btn-primary"
          >
            <Server className="w-4 h-4" />
            Deploy Honeypot
          </a>
          <a 
            href="/attacks" 
            className="btn-secondary"
          >
            <AlertTriangle className="w-4 h-4" />
            View Attacks
          </a>
          <a 
            href="/settings" 
            className="btn-secondary"
          >
            <Shield className="w-4 h-4" />
            Configure Rules
          </a>
        </div>
      </div>

      {/* System Status Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Panel */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold mb-5 flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyber-500" />
            System Status
          </h3>
          <div className="space-y-1">
            <StatusRow 
              label="API Status" 
              value="Operational" 
              status="success" 
            />
            <StatusRow 
              label="Database" 
              value="Connected" 
              status="success" 
            />
            <StatusRow 
              label="WebSocket" 
              value="Active" 
              status="success" 
            />
            <StatusRow 
              label="Attack Types Detected" 
              value={displayStats?.attacks_by_type ? Object.keys(displayStats.attacks_by_type).length.toString() : '0'} 
              status="info"
            />
            <StatusRow 
              label="Top Attacker IPs" 
              value={displayStats?.top_attackers?.length?.toString() ?? '0'} 
              status="neutral"
            />
          </div>
        </div>

        {/* Attack Types */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold mb-5 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-cyber-500" />
            Attack Types
          </h3>
          <div className="space-y-3">
            {displayStats?.attacks_by_type && Object.entries(displayStats.attacks_by_type).length > 0 ? (
              Object.entries(displayStats.attacks_by_type)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 5)
                .map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between py-2 border-b border-dark-800/50 last:border-0">
                    <span className="text-slate-300 capitalize">{type}</span>
                    <span className="text-cyber-400 font-mono">{count}</span>
                  </div>
                ))
            ) : (
              <div className="text-center py-8 text-slate-500">
                <Shield className="w-8 h-8 mx-auto mb-3 opacity-50" />
                <p>No attacks recorded yet</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Helper Components
function StatusRow({ label, value, status }: { label: string; value: string; status: 'success' | 'warning' | 'error' | 'info' | 'neutral' }) {
  const statusStyles = {
    success: 'text-emerald-400',
    warning: 'text-amber-400',
    error: 'text-red-400',
    info: 'text-cyber-400',
    neutral: 'text-slate-300',
  }
  
  return (
    <div className="flex items-center justify-between py-3 border-b border-dark-800/50 last:border-0">
      <span className="text-slate-400">{label}</span>
      <span className={`flex items-center gap-2 font-medium ${statusStyles[status]}`}>
        {status === 'success' && <span className="w-2 h-2 bg-emerald-500 rounded-full status-dot-success"></span>}
        {value}
      </span>
    </div>
  )
}