/**
 * Execution Status Component
 * Displays AI decision execution history with real-time status tracking.
 * 
 * Design System: Dark Mode (OLED) - Security Dashboard
 * - Primary: #2563EB (blue)
 * - Success: #10B981 (emerald)
 * - Warning: #F59E0B (amber)
 * - Danger: #EF4444 (red)
 * - Background: Deep blacks with subtle gradients
 */
import { useState, useEffect, useCallback } from 'react'
import {
  Activity, CheckCircle, XCircle, Clock, AlertTriangle, ArrowRight, Terminal, Network,
  Settings, RefreshCw, ChevronDown, ChevronUp, Shield, Server
} from 'lucide-react'

// Types
interface Execution {
  id: string
  decision_id: string
  action: 'monitor' | 'reconfigure' | 'isolate' | 'switch_container'
  status: 'pending' | 'running' | 'success' | 'failed' | 'rolled_back'
  timestamp: string
  details: Record<string, any>
  error: string | null
}

interface ExecutionStats {
  total: number
  success: number
  failed: number
  success_rate: number
  actions?: Record<string, number>
}

// Design tokens
const THEME = {
  bgDeep: '#020204',
  bgBase: '#0a0a0f',
  bgElevated: '#12121a',
  bgCard: 'rgba(18, 18, 26, 0.8)',
  border: 'rgba(255, 255, 255, 0.06)',
  borderGlow: 'rgba(0, 212, 255, 0.3)',
  textPrimary: '#f1f5f9',
  textSecondary: '#94a3b8',
  textMuted: '#64748b',
  accentPrimary: '#2563EB',
  accentSecondary: '#3B82F6',
  accentSuccess: '#10B981',
  accentWarning: '#F59E0B',
  accentDanger: '#EF4444',
  accentPurple: '#8B5CF6',
}

const statusConfig = {
  pending: {
    color: THEME.textMuted,
    bg: 'rgba(100, 116, 139, 0.1)',
    border: 'rgba(100, 116, 139, 0.3)',
    icon: Clock,
    label: 'Pending',
    pulse: false
  },
  running: {
    color: THEME.accentWarning,
    bg: 'rgba(245, 158, 11, 0.1)',
    border: 'rgba(245, 158, 11, 0.3)',
    icon: RefreshCw,
    label: 'Running',
    pulse: true
  },
  success: {
    color: THEME.accentSuccess,
    bg: 'rgba(16, 185, 129, 0.1)',
    border: 'rgba(16, 185, 129, 0.3)',
    icon: CheckCircle,
    label: 'Success',
    pulse: false
  },
  failed: {
    color: THEME.accentDanger,
    bg: 'rgba(239, 68, 68, 0.1)',
    border: 'rgba(239, 68, 68, 0.3)',
    icon: XCircle,
    label: 'Failed',
    pulse: false
  },
  rolled_back: {
    color: THEME.accentPurple,
    bg: 'rgba(139, 92, 246, 0.1)',
    border: 'rgba(139, 92, 246, 0.3)',
    icon: ArrowRight,
    label: 'Rolled Back',
    pulse: false
  },
}

const actionConfig = {
  monitor: {
    color: THEME.textSecondary,
    bg: 'rgba(148, 163, 184, 0.1)',
    icon: Activity,
    label: 'Monitor',
    description: 'Observing without action'
  },
  reconfigure: {
    color: THEME.accentPrimary,
    bg: 'rgba(37, 99, 235, 0.1)',
    icon: Settings,
    label: 'Reconfigure',
    description: 'Modifying container settings'
  },
  isolate: {
    color: THEME.accentWarning,
    bg: 'rgba(245, 158, 11, 0.1)',
    icon: Network,
    label: 'Isolate',
    description: 'Moving to quarantined network'
  },
  switch_container: {
    color: THEME.accentPurple,
    bg: 'rgba(139, 92, 246, 0.1)',
    icon: Server,
    label: 'Switch Container',
    description: 'Migrating to new container'
  },
}

interface ExecutionStatusProps {
  className?: string
}

export default function ExecutionStatus({ className = '' }: ExecutionStatusProps) {
  const [executions, setExecutions] = useState<Execution[]>([])
  const [stats, setStats] = useState<ExecutionStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const fetchExecutions = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      const headers = { 'Authorization': `Bearer ${token}` }

      const response = await fetch('/api/v1/ai/executions?limit=20', { headers })
      if (response.ok) {
        const data = await response.json()
        setExecutions(data.executions || [])
        setStats(data.stats || null)
      }
    } catch (error) {
      console.error('Failed to fetch executions:', error)
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchExecutions()
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchExecutions, 5000)
    return () => clearInterval(interval)
  }, [fetchExecutions])

  const handleRefresh = () => {
    setIsRefreshing(true)
    fetchExecutions()
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const formatTimeAgo = (timestamp: string) => {
    const seconds = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000)
    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    return `${Math.floor(seconds / 3600)}h ago`
  }

  if (isLoading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-32 rounded-xl" style={{ background: THEME.bgElevated }} />
      </div>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard
            label="Total Executions"
            value={stats.total}
            icon={Activity}
            color={THEME.accentPrimary}
          />
          <StatCard
            label="Success Rate"
            value={`${stats.success_rate}%`}
            icon={CheckCircle}
            color={THEME.accentSuccess}
          />
          <StatCard
            label="Successful"
            value={stats.success}
            icon={Shield}
            color={THEME.accentSuccess}
          />
          <StatCard
            label="Failed"
            value={stats.failed}
            icon={AlertTriangle}
            color={stats.failed > 0 ? THEME.accentDanger : THEME.textMuted}
          />
        </div>
      )}

      {/* Action Distribution */}
      {stats && stats.actions && Object.keys(stats.actions).length > 0 && (
        <div 
          className="rounded-xl p-4"
          style={{
            background: THEME.bgCard,
            border: `1px solid ${THEME.border}`,
            backdropFilter: 'blur(10px)'
          }}
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium" style={{ color: THEME.textSecondary }}>
              Action Distribution
            </h3>
          </div>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(stats.actions).map(([action, count]) => {
              const config = actionConfig[action as keyof typeof actionConfig]
              const Icon = config?.icon || Activity
              return (
                <div
                  key={action}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                  style={{
                    background: config?.bg || 'rgba(148, 163, 184, 0.1)',
                    border: `1px solid ${config?.color || THEME.textMuted}30`
                  }}
                >
                  <Icon className="w-3.5 h-3.5" style={{ color: config?.color || THEME.textMuted }} />
                  <span className="text-xs font-medium" style={{ color: config?.color || THEME.textSecondary }}>
                    {config?.label || action}
                  </span>
                  <span 
                    className="text-xs px-1.5 py-0.5 rounded"
                    style={{ 
                      background: 'rgba(255,255,255,0.1)',
                      color: THEME.textPrimary
                    }}
                  >
                    {count}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Execution Timeline */}
      <div 
        className="rounded-xl overflow-hidden"
        style={{
          background: THEME.bgCard,
          border: `1px solid ${THEME.border}`,
          backdropFilter: 'blur(10px)'
        }}
      >
        <div 
          className="flex items-center justify-between px-4 py-3"
          style={{ borderBottom: `1px solid ${THEME.border}` }}
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4" style={{ color: THEME.accentPrimary }} />
            <h3 className="text-sm font-medium" style={{ color: THEME.textPrimary }}>
              Execution History
            </h3>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs transition-all duration-200 hover:opacity-80"
            style={{
              background: 'rgba(255,255,255,0.05)',
              color: THEME.textSecondary
            }}
            aria-label="Refresh execution history"
          >
            <RefreshCw 
              className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} 
            />
            Refresh
          </button>
        </div>

        {executions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12">
            <Activity 
              className="w-8 h-8 mb-3" 
              style={{ color: THEME.textMuted, opacity: 0.5 }} 
            />
            <p className="text-sm" style={{ color: THEME.textMuted }}>
              No executions yet
            </p>
            <p className="text-xs mt-1" style={{ color: THEME.textMuted, opacity: 0.7 }}>
              AI decisions will appear here when executed
            </p>
          </div>
        ) : (
          <div className="divide-y" style={{ borderColor: THEME.border }}>
            {executions.map((execution) => (
              <ExecutionItem
                key={execution.id}
                execution={execution}
                isExpanded={expandedId === execution.id}
                onToggle={() => setExpandedId(expandedId === execution.id ? null : execution.id)}
                formatTime={formatTime}
                formatTimeAgo={formatTimeAgo}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// Stat Card Component
function StatCard({ 
  label, 
  value, 
  icon: Icon, 
  color 
}: { 
  label: string
  value: string | number
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>
  color: string
}) {
  return (
    <div 
      className="rounded-xl p-3 transition-all duration-200 hover:scale-[1.02]"
      style={{
        background: THEME.bgCard,
        border: `1px solid ${THEME.border}`,
        backdropFilter: 'blur(10px)'
      }}
    >
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4" style={{ color }} />
        <span className="text-xs" style={{ color: THEME.textMuted }}>{label}</span>
      </div>
      <div className="text-xl font-bold" style={{ color: THEME.textPrimary }}>
        {value}
      </div>
    </div>
  )
}

// Execution Item Component
function ExecutionItem({
  execution,
  isExpanded,
  onToggle,
  formatTime,
  formatTimeAgo
}: {
  execution: Execution
  isExpanded: boolean
  onToggle: () => void
  formatTime: (t: string) => string
  formatTimeAgo: (t: string) => string
}) {
  const status = statusConfig[execution.status]
  const action = actionConfig[execution.action]
  const StatusIcon = status.icon

  return (
    <div 
      className="transition-all duration-200"
      style={{ background: isExpanded ? 'rgba(255,255,255,0.02)' : 'transparent' }}
    >
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center gap-3 text-left hover:bg-white/[0.02] transition-colors duration-150"
        aria-expanded={isExpanded}
        aria-label={`Execution ${execution.id} - ${action.label} - ${status.label}`}
      >
        {/* Status Indicator */}
        <div 
          className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${status.pulse ? 'animate-pulse' : ''}`}
          style={{ 
            background: status.bg,
            border: `1px solid ${status.border}`
          }}
        >
          <StatusIcon className="w-4 h-4" style={{ color: status.color }} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span 
              className="text-sm font-medium"
              style={{ color: action.color }}
            >
              {action.label}
            </span>
            <span 
              className="text-xs px-1.5 py-0.5 rounded"
              style={{ 
                background: action.bg,
                color: action.color
              }}
            >
              {execution.action}
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs" style={{ color: THEME.textMuted }}>
            <span>{formatTime(execution.timestamp)}</span>
            <span>·</span>
            <span>{formatTimeAgo(execution.timestamp)}</span>
            {execution.details?.honeypot_id && (
              <>
                <span>·</span>
                <span className="truncate">{execution.details.honeypot_id}</span>
              </>
            )}
          </div>
        </div>

        {/* Status Badge */}
        <div 
          className="px-2 py-1 rounded text-xs font-medium shrink-0"
          style={{ 
            background: status.bg,
            color: status.color,
            border: `1px solid ${status.border}`
          }}
        >
          {status.label}
        </div>

        {/* Expand Arrow */}
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 shrink-0" style={{ color: THEME.textMuted }} />
        ) : (
          <ChevronDown className="w-4 h-4 shrink-0" style={{ color: THEME.textMuted }} />
        )}
      </button>

      {/* Expanded Details */}
      {isExpanded && (
        <div 
          className="px-4 pb-3 pt-1 ml-11"
          style={{ borderTop: `1px solid ${THEME.border}` }}
        >
          <div className="grid gap-2 text-xs">
            <div className="flex items-start gap-2">
              <span style={{ color: THEME.textMuted }}>Execution ID:</span>
              <code 
                className="px-1.5 py-0.5 rounded"
                style={{ 
                  background: 'rgba(0,0,0,0.3)',
                  color: THEME.accentPrimary
                }}
              >
                {execution.id}
              </code>
            </div>
            <div className="flex items-start gap-2">
              <span style={{ color: THEME.textMuted }}>Decision ID:</span>
              <code 
                className="px-1.5 py-0.5 rounded"
                style={{ 
                  background: 'rgba(0,0,0,0.3)',
                  color: THEME.textSecondary
                }}
              >
                {execution.decision_id}
              </code>
            </div>
            {execution.details?.source_ip && (
              <div className="flex items-start gap-2">
                <span style={{ color: THEME.textMuted }}>Source IP:</span>
                <span style={{ color: THEME.textPrimary }}>{execution.details.source_ip}</span>
              </div>
            )}
            {execution.details?.threat_level && (
              <div className="flex items-start gap-2">
                <span style={{ color: THEME.textMuted }}>Threat Level:</span>
                <span 
                  className="px-1.5 py-0.5 rounded capitalize"
                  style={{ 
                    background: execution.details.threat_level === 'high' ? 'rgba(239, 68, 68, 0.2)' :
                               execution.details.threat_level === 'medium' ? 'rgba(245, 158, 11, 0.2)' :
                               'rgba(16, 185, 129, 0.2)',
                    color: execution.details.threat_level === 'high' ? THEME.accentDanger :
                           execution.details.threat_level === 'medium' ? THEME.accentWarning :
                           THEME.accentSuccess
                  }}
                >
                  {execution.details.threat_level}
                </span>
              </div>
            )}
            {execution.error && (
              <div 
                className="mt-2 p-2 rounded"
                style={{ 
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: `1px solid rgba(239, 68, 68, 0.3)`
                }}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <AlertTriangle className="w-3 h-3" style={{ color: THEME.accentDanger }} />
                  <span className="font-medium" style={{ color: THEME.accentDanger }}>Error</span>
                </div>
                <code className="text-xs" style={{ color: THEME.textSecondary }}>
                  {execution.error}
                </code>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}