import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Brain, Activity, Zap, AlertTriangle, Shield, Server, Cpu,
  Play, Pause, RefreshCw, CheckCircle,
  XCircle, TrendingUp, BarChart3
} from 'lucide-react'
import ExecutionStatus from '../components/AI/ExecutionStatus'

interface AIActivity {
  id: string
  timestamp: string
  status: 'idle' | 'analyzing' | 'processing' | 'reconfiguring' | 'decision' | 'error'
  action: string
  details: Record<string, any>
  duration_ms: number
  success: boolean
}

interface AIDecision {
  id: string
  timestamp: string
  source_ip: string
  threat_level: 'low' | 'medium' | 'high' | 'critical'
  threat_score: number
  reasoning: string
  action: string
  confidence: number
  mitre_attack_ids: string[]
}

interface AIStatus {
  is_running: boolean
  status: string
  pending_events: number
  total_activities: number
  total_decisions: number
  active_sessions: number
  llm_available: boolean
}

interface AIMetrics {
  total_activities: number
  successful_activities: number
  failed_activities: number
  success_rate: number
  status_distribution: Record<string, number>
  total_decisions: number
  action_distribution: Record<string, number>
  average_threat_score: number
  pending_events: number
  active_sessions: number
}

// Theme colors
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

const statusConfig = {
  idle: { color: '#64748b', bg: 'rgba(100, 116, 139, 0.1)', icon: Activity },
  analyzing: { color: '#00d4ff', bg: 'rgba(0, 212, 255, 0.1)', icon: Brain },
  processing: { color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.1)', icon: Cpu },
  reconfiguring: { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)', icon: Server },
  decision: { color: '#10b981', bg: 'rgba(16, 185, 129, 0.1)', icon: CheckCircle },
  error: { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)', icon: XCircle },
}

const threatColors = {
  low: { fill: '#10b981', bg: 'rgba(16, 185, 129, 0.1)' },
  medium: { fill: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' },
  high: { fill: '#f97316', bg: 'rgba(249, 115, 22, 0.1)' },
  critical: { fill: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
}

export default function AIMonitor() {
  const [status, setStatus] = useState<AIStatus | null>(null)
  const [activities, setActivities] = useState<AIActivity[]>([])
  const [decisions, setDecisions] = useState<AIDecision[]>([])
  const [metrics, setMetrics] = useState<AIMetrics | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Fetch initial data
  const fetchData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      const headers = { 'Authorization': `Bearer ${token}` }

      const [statusRes, activitiesRes, decisionsRes, metricsRes] = await Promise.all([
        fetch('/api/v1/ai/status', { headers }),
        fetch('/api/v1/ai/activities?limit=20', { headers }),
        fetch('/api/v1/ai/decisions?limit=10', { headers }),
        fetch('/api/v1/ai/metrics', { headers }),
      ])

      if (statusRes.ok) setStatus(await statusRes.json())
      if (activitiesRes.ok) {
        const data = await activitiesRes.json()
        setActivities(data.activities || [])
      }
      if (decisionsRes.ok) {
        const data = await decisionsRes.json()
        setDecisions(data.decisions || [])
      }
      if (metricsRes.ok) setMetrics(await metricsRes.json())

      setIsLoading(false)
    } catch (error) {
      console.error('Failed to fetch AI data:', error)
      setIsLoading(false)
    }
  }, [])

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    // Connect directly to backend to avoid VPN/proxy issues
    const wsUrl = 'ws://127.0.0.1:8000/api/v1/ai/ws'
    
    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        console.log('AI WebSocket connected')
      }

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data)
        
        switch (message.type) {
          case 'status':
            setStatus(message.data)
            break
          case 'activities':
            setActivities(message.data)
            break
          case 'activity':
            setActivities(prev => [message.data, ...prev.slice(0, 19)])
            break
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        // Reconnect after 5 seconds (longer delay to avoid spam)
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000)
      }

      ws.onerror = () => {
        // Silently handle error - onclose will trigger reconnect
        setIsConnected(false)
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      // Retry after 5 seconds
      reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000)
    }
  }, [])

  useEffect(() => {
    fetchData()
    connectWebSocket()

    return () => {
      if (wsRef.current) wsRef.current.close()
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
    }
  }, [fetchData, connectWebSocket])

  // Control functions
  const startAI = async () => {
    try {
      const token = localStorage.getItem('token')
      await fetch('/api/v1/ai/start', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      fetchData()
    } catch (error) {
      console.error('Failed to start AI:', error)
    }
  }

  const stopAI = async () => {
    try {
      const token = localStorage.getItem('token')
      await fetch('/api/v1/ai/stop', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      fetchData()
    } catch (error) {
      console.error('Failed to stop AI:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 border-4 border-dark-800 rounded-full"></div>
            <div className="absolute top-0 left-0 w-12 h-12 border-4 border-cyber-500 rounded-full border-t-transparent animate-spin"></div>
          </div>
          <p className="text-slate-500">Loading AI Monitor...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div 
            className="w-12 h-12 rounded-xl flex items-center justify-center"
            style={{ 
              background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(139, 92, 246, 0.2))',
              border: `1px solid ${THEME.borderGlow}`
            }}
          >
            <Brain className="w-6 h-6" style={{ color: THEME.accentPrimary }} />
          </div>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: THEME.textPrimary }}>
              AI Security Monitor
            </h1>
            <p className="text-sm" style={{ color: THEME.textSecondary }}>
              Real-time threat analysis and adaptive response
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Connection Status */}
          <div 
            className="flex items-center gap-2 px-3 py-1.5 rounded-full"
            style={{ 
              background: isConnected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              border: `1px solid ${isConnected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
            }}
          >
            <span 
              className="w-2 h-2 rounded-full"
              style={{ background: isConnected ? THEME.accentSuccess : THEME.accentDanger }}
            />
            <span 
              className="text-xs font-medium"
              style={{ color: isConnected ? THEME.accentSuccess : THEME.accentDanger }}
            >
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {/* Control Buttons */}
          {status?.is_running ? (
            <button
              onClick={stopAI}
              className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all"
              style={{ 
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: THEME.accentDanger
              }}
            >
              <Pause className="w-4 h-4" />
              Stop AI
            </button>
          ) : (
            <button
              onClick={startAI}
              className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all"
              style={{ 
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: THEME.accentSuccess
              }}
            >
              <Play className="w-4 h-4" />
              Start AI
            </button>
          )}

          <button
            onClick={fetchData}
            className="p-2 rounded-lg transition-all"
            style={{ 
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <RefreshCw className="w-4 h-4" style={{ color: THEME.textSecondary }} />
          </button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          title="AI Status"
          value={status?.status || 'idle'}
          subtitle={status?.is_running ? 'Running' : 'Stopped'}
          icon={Brain}
          color={status?.is_running ? THEME.accentPrimary : THEME.textSecondary}
        />
        <StatusCard
          title="Pending Events"
          value={String(status?.pending_events || 0)}
          subtitle="In queue"
          icon={Activity}
          color={THEME.accentWarning}
        />
        <StatusCard
          title="Total Decisions"
          value={String(status?.total_decisions || 0)}
          subtitle="AI actions taken"
          icon={Zap}
          color={THEME.accentSuccess}
        />
        <StatusCard
          title="Active Sessions"
          value={String(status?.active_sessions || 0)}
          subtitle="Being monitored"
          icon={Server}
          color={THEME.accentPrimary}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Feed - Takes 2 columns */}
        <div 
          className="lg:col-span-2 rounded-xl overflow-hidden"
          style={{ 
            background: `linear-gradient(135deg, ${THEME.bgElevated}, ${THEME.bgBase})`,
            border: `1px solid ${THEME.borderGlow}`
          }}
        >
          <div 
            className="px-6 py-4 border-b"
            style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}
          >
            <h2 className="text-lg font-semibold" style={{ color: THEME.textPrimary }}>
              Live Activity Feed
            </h2>
            <p className="text-xs" style={{ color: THEME.textSecondary }}>
              Real-time AI workflow operations
            </p>
          </div>
          
          <div className="p-4 space-y-2 max-h-[500px] overflow-y-auto">
            {activities.length === 0 ? (
              <div className="text-center py-8" style={{ color: THEME.textSecondary }}>
                <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No AI activities yet</p>
              </div>
            ) : (
              activities.map((activity) => (
                <ActivityItem key={activity.id} activity={activity} />
              ))
            )}
          </div>
        </div>

        {/* Decisions Panel */}
        <div 
          className="rounded-xl overflow-hidden"
          style={{ 
            background: `linear-gradient(135deg, ${THEME.bgElevated}, ${THEME.bgBase})`,
            border: `1px solid ${THEME.borderGlow}`
          }}
        >
          <div 
            className="px-6 py-4 border-b"
            style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}
          >
            <h2 className="text-lg font-semibold" style={{ color: THEME.textPrimary }}>
              AI Decisions
            </h2>
            <p className="text-xs" style={{ color: THEME.textSecondary }}>
              Threat assessments & actions
            </p>
          </div>
          
          <div className="p-4 space-y-3 max-h-[500px] overflow-y-auto">
            {decisions.length === 0 ? (
              <div className="text-center py-8" style={{ color: THEME.textSecondary }}>
                <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No decisions yet</p>
              </div>
            ) : (
              decisions.map((decision) => (
                <DecisionCard key={decision.id} decision={decision} />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Metrics Section */}
      {metrics && (
        <div 
          className="rounded-xl p-6"
          style={{ 
            background: `linear-gradient(135deg, ${THEME.bgElevated}, ${THEME.bgBase})`,
            border: `1px solid ${THEME.borderGlow}`
          }}
        >
          <h2 className="text-lg font-semibold mb-4" style={{ color: THEME.textPrimary }}>
            Performance Metrics
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <MetricItem
              label="Success Rate"
              value={`${(metrics.success_rate * 100).toFixed(1)}%`}
              icon={TrendingUp}
              color={THEME.accentSuccess}
            />
            <MetricItem
              label="Avg Threat Score"
              value={metrics.average_threat_score.toFixed(3)}
              icon={AlertTriangle}
              color={THEME.accentWarning}
            />
            <MetricItem
              label="Total Activities"
              value={String(metrics.total_activities)}
              icon={BarChart3}
              color={THEME.accentPrimary}
            />
            <MetricItem
              label="Success/Fail"
              value={`${metrics.successful_activities}/${metrics.failed_activities}`}
              icon={CheckCircle}
              color={THEME.accentSuccess}
            />
          </div>
        </div>
      )}

      {/* Execution Status Section */}
      <div>
        <h2 className="text-lg font-semibold mb-4" style={{ color: THEME.textPrimary }}>
          Decision Execution Status
        </h2>
        <ExecutionStatus />
      </div>
    </div>
  )
}

// Sub-components
function StatusCard({ title, value, subtitle, icon: Icon, color }: {
  title: string
  value: string | number
  subtitle: string
  icon: any
  color: string
}) {
  return (
    <div 
      className="rounded-xl p-4"
      style={{ 
        background: `linear-gradient(135deg, ${THEME.bgElevated}, ${THEME.bgBase})`,
        border: `1px solid ${THEME.borderGlow}`
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs uppercase tracking-wider" style={{ color: THEME.textSecondary }}>
          {title}
        </span>
        <Icon className="w-4 h-4" style={{ color }} />
      </div>
      <div className="text-2xl font-bold font-mono" style={{ color: THEME.textPrimary }}>
        {value}
      </div>
      <div className="text-xs mt-1" style={{ color: THEME.textSecondary }}>
        {subtitle}
      </div>
    </div>
  )
}

function ActivityItem({ activity }: { activity: AIActivity }) {
  const config = statusConfig[activity.status] || statusConfig.idle
  const Icon = config.icon
  const time = new Date(activity.timestamp).toLocaleTimeString()

  return (
    <div 
      className="flex items-start gap-3 p-3 rounded-lg transition-all hover:bg-white/5"
      style={{ 
        background: config.bg,
        border: '1px solid rgba(255, 255, 255, 0.03)'
      }}
    >
      <div 
        className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{ background: 'rgba(255, 255, 255, 0.05)' }}
      >
        <Icon className="w-4 h-4" style={{ color: config.color }} />
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium" style={{ color: THEME.textPrimary }}>
            {activity.action}
          </span>
          <span className="text-xs" style={{ color: THEME.textSecondary }}>
            {time}
          </span>
        </div>
        
        {Object.keys(activity.details).length > 0 && (
          <div className="mt-1 text-xs" style={{ color: THEME.textSecondary }}>
            {Object.entries(activity.details).slice(0, 2).map(([key, value]) => (
              <span key={key} className="mr-3">
                {key}: <span style={{ color: THEME.textPrimary }}>{String(value).slice(0, 30)}</span>
              </span>
            ))}
          </div>
        )}
        
        {activity.duration_ms > 0 && (
          <div className="mt-1 text-xs" style={{ color: THEME.textSecondary }}>
            Duration: {activity.duration_ms}ms
          </div>
        )}
      </div>
    </div>
  )
}

function DecisionCard({ decision }: { decision: AIDecision }) {
  const colors = threatColors[decision.threat_level] || threatColors.low

  return (
    <div 
      className="p-3 rounded-lg"
      style={{ 
        background: colors.bg,
        border: '1px solid rgba(255, 255, 255, 0.03)'
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono" style={{ color: THEME.textSecondary }}>
          {decision.source_ip}
        </span>
        <span 
          className="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
          style={{ 
            background: colors.bg,
            color: colors.fill,
            border: `1px solid ${colors.fill}`
          }}
        >
          {decision.threat_level}
        </span>
      </div>
      
      <div className="flex items-center justify-between text-xs">
        <span style={{ color: THEME.textSecondary }}>
          Score: <span style={{ color: colors.fill }}>{decision.threat_score.toFixed(2)}</span>
        </span>
        <span style={{ color: THEME.textSecondary }}>
          Action: <span style={{ color: THEME.accentPrimary }}>{decision.action}</span>
        </span>
      </div>
      
      <div className="mt-2 text-xs" style={{ color: THEME.textSecondary }}>
        Confidence: {(decision.confidence * 100).toFixed(0)}%
      </div>
      
      {decision.mitre_attack_ids.length > 0 && (
        <div className="flex gap-1 mt-2 flex-wrap">
          {decision.mitre_attack_ids.slice(0, 2).map(id => (
            <span 
              key={id}
              className="px-1.5 py-0.5 rounded text-[10px]"
              style={{ background: 'rgba(255, 255, 255, 0.05)', color: THEME.textSecondary }}
            >
              {id}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function MetricItem({ label, value, icon: Icon, color }: {
  label: string
  value: string
  icon: any
  color: string
}) {
  return (
    <div className="text-center">
      <Icon className="w-5 h-5 mx-auto mb-2" style={{ color }} />
      <div className="text-xl font-bold font-mono" style={{ color: THEME.textPrimary }}>
        {value}
      </div>
      <div className="text-xs" style={{ color: THEME.textSecondary }}>
        {label}
      </div>
    </div>
  )
}