import { useState, useEffect } from 'react'
import { format, formatDistanceToNow } from 'date-fns'
import {
  Shield,
  Filter,
  Search,
  Clock,
  Globe,
  Terminal,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Eye,
  Activity,
  Zap,
  TrendingUp,
  Wifi,
  RefreshCw,
} from 'lucide-react'
import { useAttacks, useSession, AttackEvent } from '../hooks/useApi'
import { useWebSocket } from '../hooks/useWebSocket'
import clsx from 'clsx'

const ITEMS_PER_PAGE = 15

// Real-time severity pulse animation
const severityGlow = {
  critical: 'animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.5)]',
  high: 'shadow-[0_0_10px_rgba(249,115,22,0.4)]',
  medium: 'shadow-[0_0_8px_rgba(234,179,8,0.3)]',
  low: 'shadow-[0_0_6px_rgba(34,197,94,0.3)]',
  info: 'shadow-[0_0_5px_rgba(59,130,246,0.3)]',
}

const severityColors = {
  critical: { bg: 'bg-red-500', text: 'text-red-400', border: 'border-red-500' },
  high: { bg: 'bg-orange-500', text: 'text-orange-400', border: 'border-orange-500' },
  medium: { bg: 'bg-yellow-500', text: 'text-yellow-400', border: 'border-yellow-500' },
  low: { bg: 'bg-green-500', text: 'text-green-400', border: 'border-green-500' },
  info: { bg: 'bg-blue-500', text: 'text-blue-400', border: 'border-blue-500' },
}

function Attacks() {
  const [search, setSearch] = useState('')
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [page, setPage] = useState(1)
  const [selectedAttack, setSelectedAttack] = useState<AttackEvent | null>(null)
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [liveCount, setLiveCount] = useState(0)
  const [isAutoRefresh, setIsAutoRefresh] = useState(true)

  const { data: attacks, isLoading, refetch } = useAttacks({
    severity: severityFilter !== 'all' ? severityFilter : undefined,
    limit: 100,
  })

  const { data: _session } = useSession(selectedSessionId || '')

  // WebSocket for real-time updates
  const { connected } = useWebSocket({
    onMessage: (msg: any) => {
      if (msg.type === 'attack_event') {
        setLiveCount(c => c + 1)
        if (isAutoRefresh) {
          refetch()
        }
      }
    },
  })

  // Reset live count when data refreshes
  useEffect(() => {
    if (attacks) {
      setLiveCount(0)
    }
  }, [attacks])

  const filteredAttacks = attacks?.filter((attack: AttackEvent) => {
    const matchesSearch =
      attack.source_ip.includes(search) ||
      attack.type.toLowerCase().includes(search.toLowerCase()) ||
      attack.honeypot_name.toLowerCase().includes(search.toLowerCase())
    return matchesSearch
  })

  const paginatedAttacks = filteredAttacks?.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE)
  const totalPages = Math.ceil((filteredAttacks?.length || 0) / ITEMS_PER_PAGE)

  // Calculate stats
  const totalAttacks = attacks?.length || 0
  const criticalHigh = attacks?.filter((a: AttackEvent) => 
    a.severity === 'critical' || a.severity === 'high'
  ).length || 0
  const uniqueIPs = new Set(attacks?.map((a: AttackEvent) => a.source_ip)).size || 0
  const attackTypes = new Set(attacks?.map((a: AttackEvent) => a.type)).size || 0

  // Get recent attack rate (last 5 minutes)
  const recentAttacks = attacks?.filter((a: AttackEvent) => {
    const attackTime = new Date(a.timestamp).getTime()
    return Date.now() - attackTime < 5 * 60 * 1000
  }).length || 0

  return (
    <div className="space-y-6">
      {/* Header with Live Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Shield className="w-8 h-8 text-cyan-400" />
            {connected && (
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            )}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white font-mono">Attack Monitor</h1>
            <p className="text-sm text-slate-400 flex items-center gap-2">
              {connected ? (
                <>
                  <Activity className="w-3 h-3 text-green-400" />
                  <span className="text-green-400">Live</span>
                </>
              ) : (
                <>
                  <Wifi className="w-3 h-3 text-red-400" />
                  <span className="text-red-400">Disconnected</span>
                </>
              )}
              {liveCount > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-cyan-500/20 text-cyan-400 rounded text-xs animate-pulse">
                  +{liveCount} new
                </span>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4 text-slate-400" />
          </button>
          <button
            onClick={() => setIsAutoRefresh(!isAutoRefresh)}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
              isAutoRefresh 
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            )}
          >
            {isAutoRefresh ? 'Auto-Refresh ON' : 'Auto-Refresh OFF'}
          </button>
        </div>
      </div>

      {/* Stats Cards - Enhanced */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={<Shield className="w-5 h-5" />}
          label="Total Attacks"
          value={totalAttacks}
          color="cyan"
          trend={recentAttacks > 0 ? `+${recentAttacks} in 5m` : undefined}
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          label="Critical/High"
          value={criticalHigh}
          color="orange"
          percentage={totalAttacks > 0 ? Math.round((criticalHigh / totalAttacks) * 100) : 0}
        />
        <StatCard
          icon={<Globe className="w-5 h-5" />}
          label="Unique IPs"
          value={uniqueIPs}
          color="blue"
        />
        <StatCard
          icon={<Zap className="w-5 h-5" />}
          label="Attack Types"
          value={attackTypes}
          color="purple"
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Attack List */}
        <div className="xl:col-span-2 space-y-4">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search by IP, type, or honeypot..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-900/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 transition-all font-mono"
              />
            </div>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <select
                value={severityFilter}
                onChange={(e) => {
                  setSeverityFilter(e.target.value)
                  setPage(1)
                }}
                className="pl-10 pr-8 py-2.5 bg-slate-900/50 border border-slate-700/50 rounded-lg text-sm text-white appearance-none cursor-pointer focus:outline-none focus:border-cyan-500/50 transition-all"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
                <option value="info">Info</option>
              </select>
            </div>
          </div>

          {/* Attack Table - Enhanced */}
          <div className="bg-slate-900/30 border border-slate-800/50 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-800/50 bg-slate-900/50">
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Time</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Severity</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Source</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Honeypot</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/30">
                  {isLoading ? (
                    [...Array(8)].map((_, i) => (
                      <tr key={i}>
                        <td colSpan={6} className="px-4 py-4">
                          <div className="h-4 bg-slate-800/50 rounded animate-pulse" />
                        </td>
                      </tr>
                    ))
                  ) : paginatedAttacks && paginatedAttacks.length > 0 ? (
                    paginatedAttacks.map((attack: AttackEvent, index: number) => (
                      <AttackRow
                        key={attack.id}
                        attack={attack}
                        isSelected={selectedAttack?.id === attack.id}
                        isNew={index < liveCount}
                        onClick={() => setSelectedAttack(attack)}
                        onViewSession={() => setSelectedSessionId(attack.session_id)}
                      />
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="px-4 py-16 text-center">
                        <div className="flex flex-col items-center gap-3">
                          <Shield className="w-12 h-12 text-slate-600" />
                          <p className="text-slate-500 font-medium">No attacks found</p>
                          {search && (
                            <p className="text-sm text-slate-600">Try adjusting your search</p>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800/50 bg-slate-900/30">
                <p className="text-sm text-slate-400">
                  Showing <span className="text-white">{(page - 1) * ITEMS_PER_PAGE + 1}</span> to{' '}
                  <span className="text-white">{Math.min(page * ITEMS_PER_PAGE, filteredAttacks?.length || 0)}</span> of{' '}
                  <span className="text-white">{filteredAttacks?.length || 0}</span>
                </p>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  {[...Array(Math.min(5, totalPages))].map((_, i) => {
                    const pageNum = i + 1
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum)}
                        className={clsx(
                          'w-8 h-8 rounded-lg text-sm font-medium transition-colors',
                          page === pageNum
                            ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                            : 'hover:bg-slate-800 text-slate-400'
                        )}
                      >
                        {pageNum}
                      </button>
                    )
                  })}
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Attack Details Panel */}
          {selectedAttack && (
            <div className="bg-slate-900/30 border border-slate-800/50 rounded-xl p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white font-mono">Attack Details</h3>
                <span className={clsx(
                  'px-3 py-1 rounded-full text-xs font-medium',
                  severityColors[selectedAttack.severity].bg,
                  'bg-opacity-20',
                  severityColors[selectedAttack.severity].text
                )}>
                  {selectedAttack.severity.toUpperCase()}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
                <DetailItem label="Attack ID" value={selectedAttack.id.slice(0, 12)} mono />
                <DetailItem label="Protocol" value={selectedAttack.protocol.toUpperCase()} />
                <DetailItem label="Source IP" value={selectedAttack.source_ip} mono />
                <DetailItem label="Honeypot" value={selectedAttack.honeypot_name} />
              </div>

              <div className="grid grid-cols-2 gap-4 mb-5">
                <DetailItem 
                  label="Timestamp" 
                  value={format(new Date(selectedAttack.timestamp), 'PPpp')} 
                />
                <DetailItem 
                  label="Time Ago" 
                  value={formatDistanceToNow(new Date(selectedAttack.timestamp), { addSuffix: true })} 
                />
              </div>

              {selectedAttack.payload && (
                <div className="mb-4">
                  <label className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2 block">Payload</label>
                  <pre className="p-4 bg-slate-950/50 border border-slate-800/50 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto max-h-40">
                    {typeof selectedAttack.payload === 'string'
                      ? selectedAttack.payload
                      : JSON.stringify(selectedAttack.payload, null, 2)}
                  </pre>
                </div>
              )}

              {selectedAttack.metadata && Object.keys(selectedAttack.metadata).length > 0 && (
                <div>
                  <label className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2 block">Metadata</label>
                  <pre className="p-4 bg-slate-950/50 border border-slate-800/50 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto max-h-40">
                    {JSON.stringify(selectedAttack.metadata, null, 2)}
                  </pre>
                </div>
              )}

              {selectedAttack.session_id && (
                <button
                  onClick={() => setSelectedSessionId(selectedAttack.session_id)}
                  className="mt-4 w-full py-2.5 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 rounded-lg text-cyan-400 text-sm font-medium transition-colors flex items-center justify-center gap-2"
                >
                  <Eye className="w-4 h-4" />
                  View Session Replay
                </button>
              )}
            </div>
          )}
        </div>

        {/* Right Sidebar - Live Feed */}
        <div className="xl:col-span-1 space-y-4">
          {/* Live Attack Feed */}
          <div className="bg-slate-900/30 border border-slate-800/50 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-800/50 bg-slate-900/50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-semibold text-white">Live Feed</h3>
              </div>
              {connected && (
                <span className="flex items-center gap-1.5 text-xs text-green-400">
                  <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                  Connected
                </span>
              )}
            </div>
            <div className="p-2 max-h-[500px] overflow-y-auto">
              <AttackFeed attacks={attacks?.slice(0, 15)} />
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-slate-900/30 border border-slate-800/50 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-purple-400" />
              Attack Velocity
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Last 5 min</span>
                <span className="text-sm font-mono text-white">{recentAttacks}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Last hour</span>
                <span className="text-sm font-mono text-white">
                  {attacks?.filter(a => Date.now() - new Date(a.timestamp).getTime() < 60 * 60 * 1000).length || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Attack rate</span>
                <span className="text-sm font-mono text-cyan-400">
                  {recentAttacks > 0 ? `${(recentAttacks / 5).toFixed(1)}/min` : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Session Replay Mini */}
          {selectedSessionId && (
            <div className="bg-slate-900/30 border border-slate-800/50 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-green-400" />
                Session Replay
              </h3>
              <p className="text-xs text-slate-400 font-mono truncate">{selectedSessionId}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Stat Card Component
function StatCard({ 
  icon, 
  label, 
  value, 
  color, 
  trend,
  percentage 
}: { 
  icon: React.ReactNode
  label: string
  value: number
  color: 'cyan' | 'orange' | 'blue' | 'purple'
  trend?: string
  percentage?: number
}) {
  const colors = {
    cyan: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    orange: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
    blue: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    purple: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  }

  return (
    <div className="bg-slate-900/30 border border-slate-800/50 rounded-xl p-4 hover:border-slate-700/50 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className={clsx('p-2 rounded-lg border', colors[color])}>
          {icon}
        </div>
        {trend && (
          <span className="text-xs text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full">
            {trend}
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-white font-mono mb-1">{value.toLocaleString()}</p>
      <p className="text-xs text-slate-400">{label}</p>
      {percentage !== undefined && (
        <div className="mt-2 h-1 bg-slate-800 rounded-full overflow-hidden">
          <div 
            className={clsx('h-full rounded-full', {
              'bg-cyan-500': color === 'cyan',
              'bg-orange-500': color === 'orange',
              'bg-blue-500': color === 'blue',
              'bg-purple-500': color === 'purple',
            })}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
      )}
    </div>
  )
}

// Attack Row Component
function AttackRow({ 
  attack, 
  isSelected, 
  isNew,
  onClick, 
  onViewSession 
}: { 
  attack: AttackEvent
  isSelected: boolean
  isNew: boolean
  onClick: () => void
  onViewSession: () => void
}) {
  const colors = severityColors[attack.severity]

  return (
    <tr
      onClick={onClick}
      className={clsx(
        'cursor-pointer transition-all duration-200 hover:bg-slate-800/30',
        isSelected && 'bg-slate-800/50',
        isNew && 'bg-cyan-500/5'
      )}
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-sm font-mono text-slate-300">
            {format(new Date(attack.timestamp), 'HH:mm:ss')}
          </span>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className={clsx(
          'inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border',
          colors.bg, 'bg-opacity-15',
          colors.text,
          colors.border, 'border-opacity-30',
          isNew && severityGlow[attack.severity]
        )}>
          {attack.severity.toUpperCase()}
        </span>
      </td>
      <td className="px-4 py-3">
        <span className="text-sm font-medium text-white font-mono">{attack.type}</span>
      </td>
      <td className="px-4 py-3">
        <span className="text-sm font-mono text-cyan-400">
          {attack.source_ip}
          {attack.source_port > 0 && `:${attack.source_port}`}
        </span>
      </td>
      <td className="px-4 py-3">
        <span className="text-sm text-slate-300">{attack.honeypot_name}</span>
      </td>
      <td className="px-4 py-3 text-center">
        {attack.session_id && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onViewSession()
            }}
            className="p-1.5 rounded-lg hover:bg-slate-700/50 text-slate-400 hover:text-cyan-400 transition-colors"
            title="View Session"
          >
            <Eye className="w-4 h-4" />
          </button>
        )}
      </td>
    </tr>
  )
}

// Detail Item Component
function DetailItem({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <label className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1 block">{label}</label>
      <p className={clsx('text-sm text-white', mono && 'font-mono')}>{value}</p>
    </div>
  )
}

// Simple Attack Feed Component
function AttackFeed({ attacks }: { attacks?: AttackEvent[] }) {
  if (!attacks || attacks.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500 text-sm">
        No recent attacks
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {attacks.map((attack, i) => (
        <div
          key={attack.id}
          className={clsx(
            'p-2 rounded-lg border-l-2 transition-colors hover:bg-slate-800/30',
            severityColors[attack.severity].border,
            i === 0 && 'bg-slate-800/20'
          )}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-300">{attack.type}</span>
            <span className={clsx('text-xs', severityColors[attack.severity].text)}>
              {attack.severity.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex items-center justify-between mt-1">
            <span className="text-xs text-cyan-400/70 font-mono">{attack.source_ip}</span>
            <span className="text-xs text-slate-500">
              {formatDistanceToNow(new Date(attack.timestamp), { addSuffix: true })}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}

export default Attacks