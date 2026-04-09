import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Brain, Activity, Zap, AlertTriangle, Shield, Server, Cpu,
  Play, Pause, RefreshCw, CheckCircle,
  XCircle, TrendingUp, BarChart3
} from 'lucide-react'
import ExecutionStatus from '../components/AI/ExecutionStatus'

interface LLMThought {
  chunk: string
  content: string
  source_ip: string
  timestamp: string
}

interface ExecutionUpdate {
  id: string
  decision_id: string
  action: string
  status: string
  stage: string
  timestamp: string
  details: {
    source_ip: string
    honeypot_id: string
    threat_level: string
    original_container?: {
      id: string
      name: string
      honeypot_id: string
      type: string
      port: number
      status: string
    }
    new_container?: {
      id: string
      name: string
      honeypot_id: string
      type: string
      port: number
      status: string
      image: string
    }
    deployment_plan?: {
      new_honeypot_id: string
      new_name: string
      deception_mode: string
      target_attacker: string
    }
    switch_summary?: {
      old_honeypot: string
      new_honeypot: string
      attacker_ip: string
      deception_mode: string
    }
    port_allocation?: {
      new_port: number
      method: string
    }
  }
  error?: string
}

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
  api_key_configured?: boolean
  api_key_prefix?: string
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
  // LLM thought streaming state
  const [llmThoughts, setLlmThoughts] = useState<LLMThought | null>(null)
  const [isThinking, setIsThinking] = useState(false)
  // Execution update state for Docker deployments
  const [executionUpdate, setExecutionUpdate] = useState<ExecutionUpdate | null>(null)
  const [executionHistory, setExecutionHistory] = useState<ExecutionUpdate[]>([])
  const thoughtTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  // Track component mount state for StrictMode compatibility
  const isMountedRef = useRef(true)

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
        // Deduplicate activities by id
        const activities = data.activities || []
        const seen = new Set<string>()
        const uniqueActivities = activities.filter((activity: AIActivity) => {
          if (seen.has(activity.id)) {
            return false
          }
          seen.add(activity.id)
          return true
        })
        setActivities(uniqueActivities)
      }
      if (decisionsRes.ok) {
        const data = await decisionsRes.json()
        // Deduplicate decisions by id
        const decisions = data.decisions || []
        const seen = new Set<string>()
        const uniqueDecisions = decisions.filter((decision: AIDecision) => {
          if (seen.has(decision.id)) {
            return false
          }
          seen.add(decision.id)
          return true
        })
        setDecisions(uniqueDecisions)
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
    // Don't reconnect if component is unmounted
    if (!isMountedRef.current) {
      return
    }

    // Use relative URL through Vite proxy
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ai/ws`
    
    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        // Only update state if still mounted
        if (isMountedRef.current) {
          setIsConnected(true)
          console.log('AI WebSocket connected')
        }
      }

      ws.onmessage = (event) => {
        // Only process messages if still mounted
        if (!isMountedRef.current) return
        
        try {
          const message = JSON.parse(event.data)
          
          switch (message.type) {
            case 'status':
              setStatus(message.data)
              break
            case 'activities':
              // Deduplicate activities by id
              setActivities(() => {
                const data = message.data as AIActivity[]
                const seen = new Set<string>()
                return data.filter(activity => {
                  if (seen.has(activity.id)) {
                    return false
                  }
                  seen.add(activity.id)
                  return true
                })
              })
              break
            case 'activity':
              // Add new activity only if it doesn't already exist
              setActivities(prev => {
                const newActivity = message.data as AIActivity
                // Check if activity with this ID already exists
                if (prev.some(a => a.id === newActivity.id)) {
                  return prev
                }
                return [newActivity, ...prev.slice(0, 19)]
              })
              break
            case 'decisions':
              // Replace decisions list
              setDecisions(() => {
                const data = message.data as AIDecision[]
                const seen = new Set<string>()
                return data.filter(decision => {
                  if (seen.has(decision.id)) {
                    return false
                  }
                  seen.add(decision.id)
                  return true
                })
              })
              break
            case 'decision':
              // Add new decision only if it doesn't already exist
              setDecisions(prev => {
                const newDecision = message.data as AIDecision
                // Check if decision with this ID already exists
                if (prev.some(d => d.id === newDecision.id)) {
                  return prev
                }
                return [newDecision, ...prev.slice(0, 9)]
              })
              // Clear thinking state when decision is made
              setIsThinking(false)
              break
            case 'llm_thought':
              // Update LLM thought streaming
              setLlmThoughts(message.data as LLMThought)
              setIsThinking(true)
              // Clear any existing timeout
              if (thoughtTimeoutRef.current) {
                clearTimeout(thoughtTimeoutRef.current)
              }
              // Auto-clear after 30 seconds of no updates
              thoughtTimeoutRef.current = setTimeout(() => {
                if (isMountedRef.current) {
                  setIsThinking(false)
                }
              }, 30000)
              break
            case 'execution_update':
              // Update execution progress for Docker deployments
              const execUpdate = message.data as ExecutionUpdate
              setExecutionUpdate(execUpdate)
              // Add to history if completed
              if (execUpdate.stage === 'completed') {
                setExecutionHistory(prev => [execUpdate, ...prev.slice(0, 9)])
              }
              break
            default:
              console.debug('Unknown WebSocket message type:', message.type)
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onclose = () => {
        // Only update state and reconnect if still mounted
        if (isMountedRef.current) {
          setIsConnected(false)
          // Reconnect after 5 seconds (longer delay to avoid spam)
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000)
        }
      }

      ws.onerror = () => {
        // Silently handle error - onclose will trigger reconnect
        if (isMountedRef.current) {
          setIsConnected(false)
        }
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      // Only retry if still mounted
      if (isMountedRef.current) {
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000)
      }
    }
  }, [])

  useEffect(() => {
    // Mark as mounted
    isMountedRef.current = true
    
    fetchData()
    connectWebSocket()

    return () => {
      // Mark as unmounted for StrictMode compatibility
      isMountedRef.current = false
      
      // Clear any pending reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
      
      // Only close WebSocket if it's OPEN (1) or CLOSING (2)
      // Don't close if CONNECTING (0) - let it complete or timeout naturally
      if (wsRef.current) {
        const ws = wsRef.current
        const readyState = ws.readyState
        
        // WebSocket readyState: 0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED
        if (readyState === WebSocket.OPEN || readyState === WebSocket.CLOSING) {
          ws.close()
        }
        wsRef.current = null
      }
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
      {/* API Key Warning Banner */}
      {status && !status.api_key_configured && (
        <div 
          className="rounded-xl p-4 flex items-center gap-4"
          style={{ 
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)'
          }}
        >
          <AlertTriangle className="w-6 h-6 flex-shrink-0" style={{ color: THEME.accentDanger }} />
          <div className="flex-1">
            <h3 className="font-semibold" style={{ color: THEME.accentDanger }}>
              LLM API Key Not Configured
            </h3>
            <p className="text-sm mt-1" style={{ color: THEME.textSecondary }}>
              AI analysis requires a valid API key. Set the <code className="px-1 py-0.5 rounded bg-white/5">MY_API_KEY</code> environment variable 
              with a key starting with "sk-" prefix. Current: <code className="px-1 py-0.5 rounded bg-white/5">{status.api_key_prefix || 'not set'}</code>
            </p>
          </div>
        </div>
      )}
      
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
          
          {/* Test Analysis Button */}
          <button
            onClick={async () => {
              try {
                const token = localStorage.getItem('token')
                // First start AI if not running
                if (!status?.is_running) {
                  await fetch('/api/v1/ai/start', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                  })
                }
                // Then trigger test analysis
                const res = await fetch('/api/v1/ai/test-analysis', {
                  method: 'POST',
                  headers: { 'Authorization': `Bearer ${token}` }
                })
                const data = await res.json()
                console.log('Test analysis triggered:', data)
              } catch (error) {
                console.error('Failed to trigger test analysis:', error)
              }
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all"
            style={{ 
              background: 'rgba(139, 92, 246, 0.1)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              color: '#8b5cf6'
            }}
          >
            <Brain className="w-4 h-4" />
            Test Analysis
          </button>
        </div>
      </div>

      {/* LLM Thinking Panel - Real-time thought streaming */}
      {(isThinking || llmThoughts) && (
        <div 
          className="rounded-xl overflow-hidden"
          style={{ 
            background: `linear-gradient(135deg, rgba(139, 92, 246, 0.1), ${THEME.bgBase})`,
            border: '1px solid rgba(139, 92, 246, 0.3)'
          }}
        >
          <div 
            className="px-6 py-4 border-b flex items-center gap-3"
            style={{ borderColor: 'rgba(139, 92, 246, 0.2)' }}
          >
            <div className="relative">
              <Brain className="w-5 h-5" style={{ color: '#8b5cf6' }} />
              {isThinking && (
                <span 
                  className="absolute -top-1 -right-1 w-2 h-2 rounded-full animate-pulse"
                  style={{ background: '#8b5cf6' }}
                />
              )}
            </div>
            <div>
              <h2 className="text-lg font-semibold" style={{ color: THEME.textPrimary }}>
                LLM Analysis Stream
              </h2>
              <p className="text-xs" style={{ color: THEME.textSecondary }}>
                {isThinking ? 'Analyzing threat data...' : 'Analysis complete'}
                {llmThoughts && ` • IP: ${llmThoughts.source_ip}`}
              </p>
            </div>
          </div>
          
          <div className="p-4">
            <div 
              className="font-mono text-sm p-4 rounded-lg max-h-[300px] overflow-y-auto"
              style={{ 
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid rgba(139, 92, 246, 0.1)'
              }}
            >
              <pre className="whitespace-pre-wrap break-words" style={{ color: THEME.textPrimary }}>
                {llmThoughts?.content || 'Waiting for LLM response...'}
              </pre>
            </div>
            
            {llmThoughts && (
              <div className="mt-3 flex items-center gap-4 text-xs" style={{ color: THEME.textSecondary }}>
                <span>
                  Characters: {llmThoughts.content?.length || 0}
                </span>
                <span>
                  Updated: {new Date(llmThoughts.timestamp).toLocaleTimeString()}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

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
              value={metrics.total_activities > 0 ? `${(metrics.success_rate * 100).toFixed(1)}%` : 'N/A'}
              icon={TrendingUp}
              color={THEME.accentSuccess}
            />
            <MetricItem
              label="Avg Threat Score"
              value={metrics.total_decisions > 0 ? metrics.average_threat_score.toFixed(3) : 'N/A'}
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
              value={metrics.total_activities > 0 ? `${metrics.successful_activities}/${metrics.failed_activities}` : '0/0'}
              icon={CheckCircle}
              color={THEME.accentSuccess}
            />
          </div>
        </div>
      )}

      {/* Docker Deployment Panel - Shows real-time container deployment */}
      {(executionUpdate || executionHistory.length > 0) && (
        <div 
          className="rounded-xl overflow-hidden"
          style={{ 
            background: `linear-gradient(135deg, rgba(16, 185, 129, 0.1), ${THEME.bgBase})`,
            border: '1px solid rgba(16, 185, 129, 0.3)'
          }}
        >
          <div 
            className="px-6 py-4 border-b flex items-center gap-3"
            style={{ borderColor: 'rgba(16, 185, 129, 0.2)' }}
          >
            <div className="relative">
              <Server className="w-5 h-5" style={{ color: THEME.accentSuccess }} />
              {executionUpdate && executionUpdate.stage !== 'completed' && (
                <span 
                  className="absolute -top-1 -right-1 w-2 h-2 rounded-full animate-pulse"
                  style={{ background: THEME.accentSuccess }}
                />
              )}
            </div>
            <div>
              <h2 className="text-lg font-semibold" style={{ color: THEME.textPrimary }}>
                Docker Deployment
              </h2>
              <p className="text-xs" style={{ color: THEME.textSecondary }}>
                {executionUpdate?.stage === 'completed' 
                  ? 'Deployment complete' 
                  : executionUpdate?.stage 
                    ? `Stage: ${executionUpdate.stage.replace(/_/g, ' ')}`
                    : 'Recent deployments'}
              </p>
            </div>
          </div>
          
          <div className="p-4 space-y-4">
            {/* Current/Latest Deployment */}
            {executionUpdate && (
              <div 
                className="p-4 rounded-lg"
                style={{ 
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid rgba(16, 185, 129, 0.2)'
                }}
              >
                {/* Status Bar */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span 
                      className="px-2 py-1 rounded text-xs font-bold uppercase"
                      style={{ 
                        background: executionUpdate.status === 'success' ? 'rgba(16, 185, 129, 0.2)' : 
                                   executionUpdate.status === 'failed' ? 'rgba(239, 68, 68, 0.2)' : 
                                   'rgba(245, 158, 11, 0.2)',
                        color: executionUpdate.status === 'success' ? THEME.accentSuccess : 
                               executionUpdate.status === 'failed' ? THEME.accentDanger : 
                               THEME.accentWarning
                      }}
                    >
                      {executionUpdate.status}
                    </span>
                    <span className="text-sm font-mono" style={{ color: THEME.textPrimary }}>
                      {executionUpdate.action}
                    </span>
                  </div>
                  <span className="text-xs" style={{ color: THEME.textSecondary }}>
                    {new Date(executionUpdate.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                {/* Container Switch Visualization */}
                {executionUpdate.details.original_container && executionUpdate.details.new_container && (
                  <div className="flex items-center gap-4 mb-4">
                    {/* Original Container */}
                    <div 
                      className="flex-1 p-3 rounded-lg"
                      style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)' }}
                    >
                      <div className="text-xs uppercase tracking-wider mb-2" style={{ color: THEME.textSecondary }}>
                        Original Container
                      </div>
                      <div className="font-mono text-sm" style={{ color: THEME.textPrimary }}>
                        {executionUpdate.details.original_container.name}
                      </div>
                      <div className="text-xs mt-1" style={{ color: THEME.textSecondary }}>
                        ID: {executionUpdate.details.original_container.id}
                      </div>
                      <div className="text-xs" style={{ color: THEME.textSecondary }}>
                        Port: {executionUpdate.details.original_container.port}
                      </div>
                    </div>

                    {/* Arrow */}
                    <div className="flex-shrink-0">
                      <Zap className="w-6 h-6" style={{ color: THEME.accentPrimary }} />
                    </div>

                    {/* New Container */}
                    <div 
                      className="flex-1 p-3 rounded-lg"
                      style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)' }}
                    >
                      <div className="text-xs uppercase tracking-wider mb-2" style={{ color: THEME.textSecondary }}>
                        New Container
                      </div>
                      <div className="font-mono text-sm" style={{ color: THEME.accentSuccess }}>
                        {executionUpdate.details.new_container.name}
                      </div>
                      <div className="text-xs mt-1" style={{ color: THEME.textSecondary }}>
                        ID: {executionUpdate.details.new_container.id}
                      </div>
                      <div className="text-xs" style={{ color: THEME.textSecondary }}>
                        Port: {executionUpdate.details.new_container.port}
                      </div>
                    </div>
                  </div>
                )}

                {/* Deployment Details */}
                {executionUpdate.details.switch_summary && (
                  <div 
                    className="p-3 rounded-lg"
                    style={{ background: 'rgba(255, 255, 255, 0.03)' }}
                  >
                    <div className="text-xs uppercase tracking-wider mb-2" style={{ color: THEME.textSecondary }}>
                      Switch Summary
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span style={{ color: THEME.textSecondary }}>From: </span>
                        <span className="font-mono" style={{ color: THEME.textPrimary }}>
                          {executionUpdate.details.switch_summary.old_honeypot}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: THEME.textSecondary }}>To: </span>
                        <span className="font-mono" style={{ color: THEME.accentSuccess }}>
                          {executionUpdate.details.switch_summary.new_honeypot}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: THEME.textSecondary }}>Attacker: </span>
                        <span className="font-mono" style={{ color: THEME.accentDanger }}>
                          {executionUpdate.details.switch_summary.attacker_ip}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: THEME.textSecondary }}>Mode: </span>
                        <span style={{ color: THEME.accentPrimary }}>
                          {executionUpdate.details.switch_summary.deception_mode}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Error Display */}
                {executionUpdate.error && (
                  <div 
                    className="mt-3 p-3 rounded-lg"
                    style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)' }}
                  >
                    <div className="text-xs" style={{ color: THEME.accentDanger }}>
                      Error: {executionUpdate.error}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Deployment History */}
            {executionHistory.length > 1 && (
              <div>
                <div className="text-xs uppercase tracking-wider mb-2" style={{ color: THEME.textSecondary }}>
                  Recent Deployments
                </div>
                <div className="space-y-2">
                  {executionHistory.slice(1, 4).map((exec) => (
                    <div 
                      key={exec.id}
                      className="flex items-center justify-between p-2 rounded"
                      style={{ background: 'rgba(255, 255, 255, 0.03)' }}
                    >
                      <div className="flex items-center gap-2">
                        <span 
                          className="w-2 h-2 rounded-full"
                          style={{ 
                            background: exec.status === 'success' ? THEME.accentSuccess : 
                                       exec.status === 'failed' ? THEME.accentDanger : 
                                       THEME.accentWarning
                          }}
                        />
                        <span className="text-xs font-mono" style={{ color: THEME.textPrimary }}>
                          {exec.action}
                        </span>
                        {exec.details.new_container && (
                          <span className="text-xs" style={{ color: THEME.textSecondary }}>
                            → {exec.details.new_container.name}
                          </span>
                        )}
                      </div>
                      <span className="text-xs" style={{ color: THEME.textSecondary }}>
                        {new Date(exec.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
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