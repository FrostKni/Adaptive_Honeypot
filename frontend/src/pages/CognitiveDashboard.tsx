import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Brain, Target, TrendingUp, TrendingDown, Shield,
  Eye, Lightbulb, PieChart,
  BarChart3, Users, MessageSquare, GitBranch, BookOpen, Trophy,
  Layers, RefreshCw, Filter, Search
} from 'lucide-react'

// Types for Cognitive Data
interface DetectedBias {
  bias_type: string
  confidence: number
  signals_matched: string[]
  signal_scores: Record<string, number>
}

interface MentalModel {
  beliefs: Record<string, { confidence: number; evidence: string[] }>
  knowledge: string[]
  goals: string[]
  expectations: Record<string, number>
  confidence: number
}

interface CognitiveMetrics {
  overconfidence_score: number
  persistence_score: number
  tunnel_vision_score: number
  curiosity_score: number
  exploitation_potential: number
  adaptability_score: number
}

interface DeceptionMetrics {
  total_applied: number
  successful: number
  success_rate: number
  suspicion_level: number
  by_strategy: Record<string, { applied: number; successful: number }>
}

interface CognitiveSession {
  session_id: string
  source_ip: string
  started_at: string
  last_activity: string
  biases: DetectedBias[]
  mental_model: MentalModel
  cognitive_metrics: CognitiveMetrics
  deception_metrics: DeceptionMetrics
  commands: CommandEntry[]
  active: boolean
}

interface CommandEntry {
  timestamp: string
  command: string
  deception_strategy?: string
  response_indicators: string[]
  suspicion_change: number
}

// Bias Types
const BIAS_TYPES = [
  'confirmation_bias',
  'sunk_cost',
  'dunning_kruger',
  'anchoring',
  'curiosity_gap',
  'loss_aversion',
  'availability_heuristic',
  'gambler_fallacy'
] as const

// Deception Strategies
const DECEPTION_STRATEGIES = [
  'confirm_expected_files',
  'confirm_vulnerability',
  'reward_persistence',
  'near_miss_hint',
  'false_confidence',
  'partial_success_feedback',
  'weak_first_impression',
  'tease_hidden_value',
  'breadcrumb_trail',
  'create_fomo',
  'easy_path_visibility'
] as const

// Theme colors
const THEME = {
  bgDeep: '#020204',
  bgBase: '#0a0a0f',
  bgElevated: '#12121a',
  accentPrimary: '#00d4ff',
  accentSecondary: '#8b5cf6',
  accentSuccess: '#10b981',
  accentDanger: '#ef4444',
  accentWarning: '#f59e0b',
  textPrimary: '#f1f5f9',
  textSecondary: '#94a3b8',
  borderGlow: 'rgba(0, 212, 255, 0.3)',
}

// Bias color mapping
const BIAS_COLORS: Record<string, string> = {
  confirmation_bias: '#00d4ff',
  sunk_cost: '#f59e0b',
  dunning_kruger: '#8b5cf6',
  anchoring: '#10b981',
  curiosity_gap: '#f97316',
  loss_aversion: '#ef4444',
  availability_heuristic: '#06b6d4',
  gambler_fallacy: '#a855f7',
}

// Strategy color mapping
const STRATEGY_COLORS: Record<string, string> = {
  confirm_expected_files: '#00d4ff',
  confirm_vulnerability: '#ef4444',
  reward_persistence: '#10b981',
  near_miss_hint: '#f59e0b',
  false_confidence: '#8b5cf6',
  partial_success_feedback: '#06b6d4',
  weak_first_impression: '#f97316',
  tease_hidden_value: '#ec4899',
  breadcrumb_trail: '#84cc16',
  create_fomo: '#a855f7',
  easy_path_visibility: '#14b8a6',
}

export default function CognitiveDashboard() {
  const [sessions, setSessions] = useState<CognitiveSession[]>([])
  const [selectedSession, setSelectedSession] = useState<CognitiveSession | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [commandFeed, setCommandFeed] = useState<CommandEntry[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterBias, setFilterBias] = useState<string>('all')
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Fetch initial data
  const fetchData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      const headers = { 'Authorization': `Bearer ${token}` }

      const response = await fetch('/api/v1/cognitive/sessions', { headers })
      if (response.ok) {
        const data = await response.json()
        setSessions(data.sessions || [])
      }
      setIsLoading(false)
    } catch (error) {
      console.error('Failed to fetch cognitive data:', error)
      setIsLoading(false)
    }
  }, [])

  // Use a ref to track selected session ID without triggering re-renders
  const selectedSessionIdRef = useRef<string | null>(null)
  
  // Keep the ref in sync with state
  useEffect(() => {
    selectedSessionIdRef.current = selectedSession?.session_id ?? null
  }, [selectedSession?.session_id])

  // WebSocket connection for real-time updates
  const connectWebSocket = useCallback(() => {
    // Use relative URL through Vite proxy
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/cognitive/ws`
    
    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
      }

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data)
        
        switch (message.type) {
          case 'session_update':
            setSessions(prev => {
              const idx = prev.findIndex(s => s.session_id === message.data.session_id)
              if (idx >= 0) {
                const updated = [...prev]
                updated[idx] = message.data
                return updated
              }
              return [message.data, ...prev]
            })
            // Use ref to check if we should update selected session
            if (selectedSessionIdRef.current === message.data.session_id) {
              setSelectedSession(message.data)
            }
            break
          case 'command':
            setCommandFeed(prev => [message.data, ...prev.slice(0, 49)])
            break
          case 'bias_detected':
            // Use ref to check if we should update selected session
            if (selectedSessionIdRef.current === message.data.session_id) {
              setSelectedSession(prev => prev ? {
                ...prev,
                biases: [...prev.biases, message.data.bias]
              } : null)
            }
            break
          case 'mental_model_update':
            // Use ref to check if we should update selected session
            if (selectedSessionIdRef.current === message.data.session_id) {
              setSelectedSession(prev => prev ? {
                ...prev,
                mental_model: message.data.mental_model
              } : null)
            }
            break
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000)
      }

      ws.onerror = () => {
        setIsConnected(false)
      }
    } catch (error) {
      reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000)
    }
  }, []) // No dependencies - use ref for selected session check

  useEffect(() => {
    fetchData()
    connectWebSocket()

    return () => {
      if (wsRef.current) wsRef.current.close()
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
    }
  }, [fetchData, connectWebSocket])

  // Calculate aggregate metrics
  const aggregateMetrics = {
    totalSessions: sessions.length,
    activeSessions: sessions.filter(s => s.active).length,
    totalBiases: sessions.reduce((sum, s) => sum + s.biases.length, 0),
    avgConfidence: sessions.length > 0 
      ? sessions.reduce((sum, s) => sum + s.cognitive_metrics.overconfidence_score, 0) / sessions.length 
      : 0,
    deceptionSuccessRate: sessions.length > 0
      ? sessions.reduce((sum, s) => sum + s.deception_metrics.success_rate, 0) / sessions.length
      : 0,
    avgSuspicion: sessions.length > 0
      ? sessions.reduce((sum, s) => sum + s.deception_metrics.suspicion_level, 0) / sessions.length
      : 0,
  }

  // Calculate bias distribution for pie chart
  const biasDistribution = BIAS_TYPES.reduce((acc, type) => {
    const count = sessions.reduce((sum, s) => 
      sum + s.biases.filter(b => b.bias_type === type).length, 0)
    if (count > 0) acc[type] = count
    return acc
  }, {} as Record<string, number>)

  // Calculate strategy effectiveness for bar chart
  const strategyEffectiveness = DECEPTION_STRATEGIES.reduce((acc, strategy) => {
    const stats = sessions.reduce((sum, s) => {
      const stratData = s.deception_metrics.by_strategy[strategy]
      if (stratData) {
        sum.applied += stratData.applied
        sum.successful += stratData.successful
      }
      return sum
    }, { applied: 0, successful: 0 })
    
    if (stats.applied > 0) {
      acc[strategy] = {
        ...stats,
        rate: stats.applied > 0 ? stats.successful / stats.applied : 0
      }
    }
    return acc
  }, {} as Record<string, { applied: number; successful: number; rate: number }>)

  // Filter sessions
  const filteredSessions = sessions.filter(session => {
    const matchesSearch = session.source_ip.includes(searchTerm) ||
      session.session_id.includes(searchTerm)
    const matchesFilter = filterBias === 'all' || 
      session.biases.some(b => b.bias_type === filterBias)
    return matchesSearch && matchesFilter
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-slate-800 rounded-full"></div>
            <div className="absolute top-0 left-0 w-16 h-16 border-4 border-cyan-500 rounded-full border-t-transparent animate-spin"></div>
          </div>
          <p className="text-slate-500">Loading Cognitive Dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div 
            className="w-12 h-12 rounded-xl flex items-center justify-center"
            style={{ 
              background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(0, 212, 255, 0.2))',
              border: `1px solid ${THEME.borderGlow}`
            }}
          >
            <Brain className="w-6 h-6" style={{ color: THEME.accentSecondary }} />
          </div>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: THEME.textPrimary }}>
              Cognitive Security Dashboard
            </h1>
            <p className="text-sm" style={{ color: THEME.textSecondary }}>
              Real-time attacker psychology analysis and deception metrics
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
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
              {isConnected ? 'Live' : 'Disconnected'}
            </span>
          </div>

          <button
            onClick={fetchData}
            className="p-2 rounded-lg transition-all hover:bg-slate-800"
            style={{ border: '1px solid rgba(255, 255, 255, 0.1)' }}
          >
            <RefreshCw className="w-4 h-4" style={{ color: THEME.textSecondary }} />
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Sessions"
          value={aggregateMetrics.activeSessions}
          subtitle={`of ${aggregateMetrics.totalSessions} total`}
          icon={Users}
          color={THEME.accentPrimary}
        />
        <StatCard
          title="Detected Biases"
          value={aggregateMetrics.totalBiases}
          subtitle="Across all sessions"
          icon={Target}
          color={THEME.accentSecondary}
        />
        <StatCard
          title="Deception Success"
          value={`${(aggregateMetrics.deceptionSuccessRate * 100).toFixed(1)}%`}
          subtitle="Strategy effectiveness"
          icon={Trophy}
          color={THEME.accentSuccess}
        />
        <StatCard
          title="Avg Suspicion Level"
          value={`${(aggregateMetrics.avgSuspicion * 100).toFixed(0)}%`}
          subtitle="Attacker awareness"
          icon={Eye}
          color={aggregateMetrics.avgSuspicion > 0.5 ? THEME.accentWarning : THEME.accentSuccess}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Session List */}
        <div className="lg:col-span-1 space-y-4">
          {/* Search and Filter */}
          <div className="glass-card p-4 space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search by IP or session ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-500" />
              <select
                value={filterBias}
                onChange={(e) => setFilterBias(e.target.value)}
                className="select flex-1"
              >
                <option value="all">All Biases</option>
                {BIAS_TYPES.map(type => (
                  <option key={type} value={type}>
                    {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Session List */}
          <div 
            className="rounded-xl overflow-hidden"
            style={{ 
              background: `linear-gradient(135deg, ${THEME.bgElevated}, ${THEME.bgBase})`,
              border: `1px solid ${THEME.borderGlow}`
            }}
          >
            <div 
              className="px-4 py-3 border-b"
              style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}
            >
              <h2 className="text-sm font-semibold" style={{ color: THEME.textPrimary }}>
                Sessions
              </h2>
            </div>
            <div className="max-h-[400px] overflow-y-auto">
              {filteredSessions.length === 0 ? (
                <div className="p-8 text-center" style={{ color: THEME.textSecondary }}>
                  <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No sessions found</p>
                </div>
              ) : (
                filteredSessions.map(session => (
                  <SessionItem
                    key={session.session_id}
                    session={session}
                    isSelected={selectedSession?.session_id === session.session_id}
                    onClick={() => setSelectedSession(session)}
                  />
                ))
              )}
            </div>
          </div>
        </div>

        {/* Middle & Right Columns */}
        <div className="lg:col-span-2 space-y-6">
          {/* Bias Distribution Pie Chart & Strategy Effectiveness Bar Chart */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Bias Distribution */}
            <div 
              className="rounded-xl p-4"
              style={{ 
                background: `linear-gradient(135deg, ${THEME.bgElevated}, ${THEME.bgBase})`,
                border: `1px solid ${THEME.borderGlow}`
              }}
            >
              <div className="flex items-center gap-2 mb-4">
                <PieChart className="w-5 h-5" style={{ color: THEME.accentPrimary }} />
                <h3 className="text-sm font-semibold" style={{ color: THEME.textPrimary }}>
                  Bias Distribution
                </h3>
              </div>
              <BiasPieChart data={biasDistribution} />
            </div>

            {/* Strategy Effectiveness */}
            <div 
              className="rounded-xl p-4"
              style={{ 
                background: `linear-gradient(135deg, ${THEME.bgElevated}, ${THEME.bgBase})`,
                border: `1px solid ${THEME.borderGlow}`
              }}
            >
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="w-5 h-5" style={{ color: THEME.accentSuccess }} />
                <h3 className="text-sm font-semibold" style={{ color: THEME.textPrimary }}>
                  Strategy Effectiveness
                </h3>
              </div>
              <StrategyBarChart data={strategyEffectiveness} />
            </div>
          </div>

          {/* Mental Model Visualization */}
          {selectedSession && (
            <div 
              className="rounded-xl overflow-hidden"
              style={{ 
                background: `linear-gradient(135deg, ${THEME.bgElevated}, ${THEME.bgBase})`,
                border: `1px solid ${THEME.borderGlow}`
              }}
            >
              <div 
                className="px-4 py-3 border-b flex items-center gap-2"
                style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}
              >
                <Brain className="w-5 h-5" style={{ color: THEME.accentSecondary }} />
                <h3 className="text-sm font-semibold" style={{ color: THEME.textPrimary }}>
                  Mental Model - {selectedSession.source_ip}
                </h3>
              </div>
              <div className="p-4">
                <MentalModelVisualization mentalModel={selectedSession.mental_model} />
              </div>
            </div>
          )}

          {/* Live Command Feed */}
          <div 
            className="rounded-xl overflow-hidden"
            style={{ 
              background: `linear-gradient(135deg, ${THEME.bgElevated}, ${THEME.bgBase})`,
              border: `1px solid ${THEME.borderGlow}`
            }}
          >
            <div 
              className="px-4 py-3 border-b flex items-center justify-between"
              style={{ borderColor: 'rgba(255, 255, 255, 0.05)' }}
            >
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" style={{ color: THEME.accentPrimary }} />
                <h3 className="text-sm font-semibold" style={{ color: THEME.textPrimary }}>
                  Live Command Feed
                </h3>
              </div>
              {selectedSession && (
                <span className="text-xs px-2 py-1 rounded bg-cyan-500/10 text-cyan-400">
                  {selectedSession.source_ip}
                </span>
              )}
            </div>
            <div className="max-h-[300px] overflow-y-auto">
              {commandFeed.length === 0 && selectedSession?.commands.length === 0 ? (
                <div className="p-8 text-center" style={{ color: THEME.textSecondary }}>
                  <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No commands yet</p>
                </div>
              ) : (
                (selectedSession?.commands || commandFeed).map((cmd, idx) => (
                  <CommandFeedItem key={idx} command={cmd} />
                ))
              )}
            </div>
          </div>

          {/* Cognitive Metrics & Deception Metrics */}
          {selectedSession && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Cognitive Metrics */}
              <div 
                className="rounded-xl p-4"
                style={{ 
                  background: `linear-gradient(135deg, ${THEME.bgElevated}, ${THEME.bgBase})`,
                  border: `1px solid ${THEME.borderGlow}`
                }}
              >
                <div className="flex items-center gap-2 mb-4">
                  <Layers className="w-5 h-5" style={{ color: THEME.accentWarning }} />
                  <h3 className="text-sm font-semibold" style={{ color: THEME.textPrimary }}>
                    Cognitive Metrics
                  </h3>
                </div>
                <div className="space-y-3">
                  <MetricBar 
                    label="Overconfidence" 
                    value={selectedSession.cognitive_metrics.overconfidence_score} 
                    color={THEME.accentDanger}
                  />
                  <MetricBar 
                    label="Persistence" 
                    value={selectedSession.cognitive_metrics.persistence_score} 
                    color={THEME.accentWarning}
                  />
                  <MetricBar 
                    label="Tunnel Vision" 
                    value={selectedSession.cognitive_metrics.tunnel_vision_score} 
                    color={THEME.accentSecondary}
                  />
                  <MetricBar 
                    label="Curiosity" 
                    value={selectedSession.cognitive_metrics.curiosity_score} 
                    color={THEME.accentPrimary}
                  />
                  <MetricBar 
                    label="Exploitation Potential" 
                    value={selectedSession.cognitive_metrics.exploitation_potential} 
                    color={THEME.accentSuccess}
                  />
                </div>
              </div>

              {/* Deception Metrics */}
              <div 
                className="rounded-xl p-4"
                style={{ 
                  background: `linear-gradient(135deg, ${THEME.bgElevated}, ${THEME.bgBase})`,
                  border: `1px solid ${THEME.borderGlow}`
                }}
              >
                <div className="flex items-center gap-2 mb-4">
                  <Shield className="w-5 h-5" style={{ color: THEME.accentSuccess }} />
                  <h3 className="text-sm font-semibold" style={{ color: THEME.textPrimary }}>
                    Deception Metrics
                  </h3>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm" style={{ color: THEME.textSecondary }}>Total Applied</span>
                    <span className="font-mono text-lg" style={{ color: THEME.textPrimary }}>
                      {selectedSession.deception_metrics.total_applied}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm" style={{ color: THEME.textSecondary }}>Successful</span>
                    <span className="font-mono text-lg" style={{ color: THEME.accentSuccess }}>
                      {selectedSession.deception_metrics.successful}
                    </span>
                  </div>
                  <MetricBar 
                    label="Success Rate" 
                    value={selectedSession.deception_metrics.success_rate} 
                    color={THEME.accentSuccess}
                  />
                  <MetricBar 
                    label="Suspicion Level" 
                    value={selectedSession.deception_metrics.suspicion_level} 
                    color={selectedSession.deception_metrics.suspicion_level > 0.5 ? THEME.accentDanger : THEME.accentSuccess}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Sub-components

function StatCard({ title, value, subtitle, icon: Icon, color }: {
  title: string
  value: string | number
  subtitle: string
  icon: any
  color: string
}) {
  return (
    <div 
      className="rounded-xl p-4 stat-card"
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

function SessionItem({ session, isSelected, onClick }: {
  session: CognitiveSession
  isSelected: boolean
  onClick: () => void
}) {
  const dominantBias = session.biases.length > 0 
    ? session.biases.reduce((a, b) => a.confidence > b.confidence ? a : b)
    : null

  return (
    <div 
      onClick={onClick}
      className="px-4 py-3 cursor-pointer transition-all border-b border-slate-800/50 last:border-0"
      style={{ 
        background: isSelected ? 'rgba(0, 212, 255, 0.05)' : 'transparent',
        borderLeft: isSelected ? '2px solid #00d4ff' : '2px solid transparent'
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-sm" style={{ color: THEME.textPrimary }}>
          {session.source_ip}
        </span>
        <span 
          className="w-2 h-2 rounded-full"
          style={{ background: session.active ? THEME.accentSuccess : THEME.textSecondary }}
        />
      </div>
      <div className="flex items-center gap-2 flex-wrap">
        {session.biases.length > 0 ? (
          session.biases.slice(0, 3).map((bias, idx) => (
            <span 
              key={idx}
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ 
                background: `${BIAS_COLORS[bias.bias_type] || THEME.accentPrimary}20`,
                color: BIAS_COLORS[bias.bias_type] || THEME.accentPrimary,
                border: `1px solid ${BIAS_COLORS[bias.bias_type] || THEME.accentPrimary}40`
              }}
            >
              {bias.bias_type.replace(/_/g, ' ').split(' ').map(w => w[0]).join('').toUpperCase()}
            </span>
          ))
        ) : (
          <span className="text-xs text-slate-500">No biases detected</span>
        )}
        {session.biases.length > 3 && (
          <span className="text-xs text-slate-500">+{session.biases.length - 3}</span>
        )}
      </div>
      {dominantBias && (
        <div className="mt-2 text-xs" style={{ color: THEME.textSecondary }}>
          Dominant: {dominantBias.bias_type.replace(/_/g, ' ')} ({(dominantBias.confidence * 100).toFixed(0)}%)
        </div>
      )}
    </div>
  )
}

function BiasPieChart({ data }: { data: Record<string, number> }) {
  const total = Object.values(data).reduce((a, b) => a + b, 0)
  if (total === 0) {
    return (
      <div className="h-48 flex items-center justify-center" style={{ color: THEME.textSecondary }}>
        <div className="text-center">
          <PieChart className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No bias data yet</p>
        </div>
      </div>
    )
  }

  let currentAngle = 0
  const segments = Object.entries(data).map(([type, count]) => {
    const percentage = count / total
    const angle = percentage * 360
    const segment = {
      type,
      count,
      percentage,
      startAngle: currentAngle,
      endAngle: currentAngle + angle,
      color: BIAS_COLORS[type] || '#64748b'
    }
    currentAngle += angle
    return segment
  })

  const size = 180
  const center = size / 2
  const radius = 70

  const describeArc = (x: number, y: number, r: number, startAngle: number, endAngle: number) => {
    const start = polarToCartesian(x, y, r, endAngle)
    const end = polarToCartesian(x, y, r, startAngle)
    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1"
    return [
      "M", x, y,
      "L", start.x, start.y,
      "A", r, r, 0, largeArcFlag, 0, end.x, end.y,
      "Z"
    ].join(" ")
  }

  const polarToCartesian = (cx: number, cy: number, r: number, angle: number) => {
    const rad = (angle - 90) * Math.PI / 180
    return {
      x: cx + r * Math.cos(rad),
      y: cy + r * Math.sin(rad)
    }
  }

  return (
    <div className="flex items-center gap-4">
      <svg width={size} height={size} className="flex-shrink-0">
        {segments.map((segment, idx) => (
          <path
            key={idx}
            d={describeArc(center, center, radius, segment.startAngle, segment.endAngle)}
            fill={segment.color}
            stroke={THEME.bgBase}
            strokeWidth="2"
            className="transition-opacity hover:opacity-80"
          />
        ))}
        <circle
          cx={center}
          cy={center}
          r={radius * 0.5}
          fill={THEME.bgBase}
        />
        <text
          x={center}
          y={center}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={THEME.textPrimary}
          fontSize="14"
          fontWeight="bold"
        >
          {total}
        </text>
      </svg>
      <div className="flex-1 space-y-1 overflow-y-auto max-h-48">
        {segments.map((segment, idx) => (
          <div key={idx} className="flex items-center gap-2 text-xs">
            <span 
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ background: segment.color }}
            />
            <span className="truncate" style={{ color: THEME.textSecondary }}>
              {segment.type.replace(/_/g, ' ')}
            </span>
            <span className="font-mono" style={{ color: THEME.textPrimary }}>
              {segment.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function StrategyBarChart({ data }: { data: Record<string, { applied: number; successful: number; rate: number }> }) {
  const entries = Object.entries(data)
  if (entries.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center" style={{ color: THEME.textSecondary }}>
        <div className="text-center">
          <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No strategy data yet</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2 max-h-56 overflow-y-auto">
      {entries
        .sort(([, a], [, b]) => b.rate - a.rate)
        .map(([strategy, stats]) => (
          <div key={strategy} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="truncate" style={{ color: THEME.textSecondary }}>
                {strategy.replace(/_/g, ' ')}
              </span>
              <span className="font-mono" style={{ color: THEME.textPrimary }}>
                {(stats.rate * 100).toFixed(0)}%
              </span>
            </div>
            <div 
              className="h-2 rounded-full overflow-hidden"
              style={{ background: 'rgba(255, 255, 255, 0.05)' }}
            >
              <div 
                className="h-full rounded-full transition-all"
                style={{ 
                  width: `${stats.rate * 100}%`,
                  background: STRATEGY_COLORS[strategy] || THEME.accentPrimary
                }}
              />
            </div>
            <div className="flex justify-between text-xs" style={{ color: THEME.textSecondary }}>
              <span>{stats.successful}/{stats.applied} successful</span>
            </div>
          </div>
        ))}
    </div>
  )
}

function MentalModelVisualization({ mentalModel }: { mentalModel: MentalModel }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Beliefs */}
      <div className="space-y-2">
        <h4 className="text-xs uppercase tracking-wider flex items-center gap-2" style={{ color: THEME.textSecondary }}>
          <Lightbulb className="w-4 h-4" />
          Beliefs
        </h4>
        <div className="space-y-2">
          {Object.entries(mentalModel.beliefs).slice(0, 5).map(([belief, data], idx) => (
            <div key={idx} className="p-2 rounded-lg" style={{ background: 'rgba(255, 255, 255, 0.02)' }}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs truncate flex-1" style={{ color: THEME.textPrimary }}>
                  {belief}
                </span>
                <span className="text-xs font-mono" style={{ color: THEME.accentPrimary }}>
                  {(data.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255, 255, 255, 0.05)' }}>
                <div 
                  className="h-full rounded-full"
                  style={{ width: `${data.confidence * 100}%`, background: THEME.accentPrimary }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Goals */}
      <div className="space-y-2">
        <h4 className="text-xs uppercase tracking-wider flex items-center gap-2" style={{ color: THEME.textSecondary }}>
          <Target className="w-4 h-4" />
          Goals
        </h4>
        <div className="space-y-1">
          {mentalModel.goals.slice(0, 5).map((goal, idx) => (
            <div 
              key={idx}
              className="p-2 rounded-lg text-xs"
              style={{ background: 'rgba(255, 255, 255, 0.02)', color: THEME.textPrimary }}
            >
              {goal}
            </div>
          ))}
        </div>
      </div>

      {/* Knowledge */}
      <div className="space-y-2">
        <h4 className="text-xs uppercase tracking-wider flex items-center gap-2" style={{ color: THEME.textSecondary }}>
          <BookOpen className="w-4 h-4" />
          Knowledge
        </h4>
        <div className="flex flex-wrap gap-1">
          {mentalModel.knowledge.slice(0, 8).map((item, idx) => (
            <span
              key={idx}
              className="text-xs px-2 py-1 rounded-full"
              style={{ 
                background: 'rgba(139, 92, 246, 0.1)',
                color: THEME.accentSecondary,
                border: '1px solid rgba(139, 92, 246, 0.2)'
              }}
            >
              {item}
            </span>
          ))}
        </div>
      </div>

      {/* Expectations */}
      <div className="space-y-2">
        <h4 className="text-xs uppercase tracking-wider flex items-center gap-2" style={{ color: THEME.textSecondary }}>
          <GitBranch className="w-4 h-4" />
          Expectations
        </h4>
        <div className="space-y-1">
          {Object.entries(mentalModel.expectations).slice(0, 4).map(([expectation, prob], idx) => (
            <div key={idx} className="flex justify-between items-center text-xs">
              <span className="truncate flex-1" style={{ color: THEME.textPrimary }}>
                {expectation}
              </span>
              <span 
                className="font-mono px-2 py-0.5 rounded"
                style={{ 
                  color: prob > 0.7 ? THEME.accentSuccess : prob > 0.4 ? THEME.accentWarning : THEME.accentDanger
                }}
              >
                {(prob * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function CommandFeedItem({ command }: { command: CommandEntry }) {
  return (
    <div className="px-4 py-2 border-b border-slate-800/50 last:border-0 hover:bg-slate-800/30 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <code 
            className="text-xs font-mono block truncate"
            style={{ color: THEME.textPrimary }}
          >
            $ {command.command}
          </code>
          {command.deception_strategy && (
            <span 
              className="inline-block mt-1 text-xs px-2 py-0.5 rounded"
              style={{ 
                background: `${STRATEGY_COLORS[command.deception_strategy] || THEME.accentPrimary}20`,
                color: STRATEGY_COLORS[command.deception_strategy] || THEME.accentPrimary
              }}
            >
              {command.deception_strategy.replace(/_/g, ' ')}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {command.suspicion_change > 0 ? (
            <TrendingUp className="w-3 h-3" style={{ color: THEME.accentDanger }} />
          ) : command.suspicion_change < 0 ? (
            <TrendingDown className="w-3 h-3" style={{ color: THEME.accentSuccess }} />
          ) : null}
          <span className="text-xs font-mono" style={{ color: THEME.textSecondary }}>
            {new Date(command.timestamp).toLocaleTimeString()}
          </span>
        </div>
      </div>
      {command.response_indicators.length > 0 && (
        <div className="mt-1 flex flex-wrap gap-1">
          {command.response_indicators.map((indicator, idx) => (
            <span 
              key={idx}
              className="text-xs px-1.5 py-0.5 rounded"
              style={{ 
                background: 'rgba(255, 255, 255, 0.05)',
                color: THEME.textSecondary
              }}
            >
              {indicator}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function MetricBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span style={{ color: THEME.textSecondary }}>{label}</span>
        <span className="font-mono" style={{ color: THEME.textPrimary }}>
          {(value * 100).toFixed(0)}%
        </span>
      </div>
      <div 
        className="h-1.5 rounded-full overflow-hidden"
        style={{ background: 'rgba(255, 255, 255, 0.05)' }}
      >
        <div 
          className="h-full rounded-full transition-all"
          style={{ width: `${value * 100}%`, background: color }}
        />
      </div>
    </div>
  )
}