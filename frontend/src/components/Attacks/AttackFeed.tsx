import { useEffect, useRef, useState } from 'react'
import { format } from 'date-fns'
import { Shield, Terminal, Globe, Clock, ChevronDown, AlertTriangle } from 'lucide-react'
import { AttackEvent } from '../../hooks/useApi'
import { useWebSocket } from '../../hooks/useWebSocket'
import clsx from 'clsx'

interface AttackFeedProps {
  initialAttacks?: AttackEvent[]
  maxItems?: number
}

function AttackFeed({ initialAttacks = [], maxItems = 50 }: AttackFeedProps) {
  const [attacks, setAttacks] = useState<AttackEvent[]>(initialAttacks)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const feedRef = useRef<HTMLDivElement>(null)

  const { connected } = useWebSocket({
    onMessage: (message: any) => {
      if (message.type === 'attack_event') {
        const attack = message.data as AttackEvent
        setAttacks((prev) => [attack, ...prev].slice(0, maxItems))
      }
    },
  })

  // Auto-scroll to top on new attack
  useEffect(() => {
    if (autoScroll && feedRef.current) {
      feedRef.current.scrollTop = 0
    }
  }, [attacks.length, autoScroll])

  const severityColors: Record<string, string> = {
    critical: 'border-red-500 bg-red-500/10',
    high: 'border-orange-500 bg-orange-500/10',
    medium: 'border-yellow-500 bg-yellow-500/10',
    low: 'border-green-500 bg-green-500/10',
    info: 'border-blue-500 bg-blue-500/10',
  }

  const severityBadgeClass: Record<string, string> = {
    critical: 'badge-critical',
    high: 'badge-high',
    medium: 'badge-medium',
    low: 'badge-low',
    info: 'badge-info',
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return format(date, 'HH:mm:ss')
    } catch {
      return timestamp
    }
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-cyan-400" />
          <h3 className="text-lg font-semibold text-slate-100">Live Attack Feed</h3>
          {connected && (
            <span className="flex items-center gap-1.5 text-xs text-cyan-400">
              <span className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
              LIVE
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm text-slate-400">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
            />
            Auto-scroll
          </label>
        </div>
      </div>

      {/* Feed */}
      <div
        ref={feedRef}
        className="flex-1 overflow-y-auto space-y-2 pr-2"
        style={{ maxHeight: '600px' }}
      >
        {attacks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-slate-400">
            <AlertTriangle className="w-12 h-12 mb-4 opacity-50" />
            <p>No attacks detected yet</p>
            <p className="text-sm mt-1">Waiting for incoming attacks...</p>
          </div>
        ) : (
          attacks.map((attack) => (
            <div
              key={attack.id}
              className={clsx(
                'border-l-2 rounded-r-lg p-3 transition-all',
                severityColors[attack.severity] || severityColors.info
              )}
            >
              <div
                className="flex items-start justify-between cursor-pointer"
                onClick={() => setExpandedId(expandedId === attack.id ? null : attack.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={clsx('px-2 py-0.5 rounded text-xs font-medium', severityBadgeClass[attack.severity] || severityBadgeClass.info)}>
                      {attack.severity.toUpperCase()}
                    </span>
                    <span className="text-sm font-medium text-slate-200">
                      {attack.type}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-sm text-slate-400">
                    <span className="flex items-center gap-1">
                      <Globe className="w-3 h-3" />
                      {attack.source_ip}
                    </span>
                    <span className="flex items-center gap-1">
                      <Terminal className="w-3 h-3" />
                      {attack.protocol}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTimestamp(attack.timestamp)}
                    </span>
                  </div>
                </div>

                <ChevronDown
                  className={clsx(
                    'w-4 h-4 text-slate-400 transition-transform',
                    expandedId === attack.id && 'rotate-180'
                  )}
                />
              </div>

              {/* Expanded details */}
              {expandedId === attack.id && (
                <div className="mt-3 pt-3 border-t border-slate-700/50">
                  <div className="space-y-2 text-sm">
                    <div className="flex gap-2">
                      <span className="text-slate-400 w-24">Honeypot:</span>
                      <span className="text-slate-200">{attack.honeypot_name}</span>
                    </div>
                    <div className="flex gap-2">
                      <span className="text-slate-400 w-24">Source Port:</span>
                      <span className="text-slate-200 font-mono">{attack.source_port}</span>
                    </div>
                    {attack.session_id && (
                      <div className="flex gap-2">
                        <span className="text-slate-400 w-24">Session:</span>
                        <span className="text-slate-200 font-mono text-xs">{attack.session_id}</span>
                      </div>
                    )}
                    {attack.payload && (
                      <div className="mt-2">
                        <span className="text-slate-400">Payload:</span>
                        <pre className="mt-1 p-2 bg-slate-950 rounded text-xs font-mono text-slate-300 overflow-x-auto">
                          {typeof attack.payload === 'string' 
                            ? attack.payload 
                            : JSON.stringify(attack.payload, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-slate-700 flex items-center justify-between text-sm text-slate-400">
        <span>{attacks.length} attacks in feed</span>
        {attacks.length > 0 && (
          <button
            onClick={() => setAttacks([])}
            className="text-slate-400 hover:text-slate-100 transition-colors"
          >
            Clear feed
          </button>
        )}
      </div>
    </div>
  )
}

export default AttackFeed