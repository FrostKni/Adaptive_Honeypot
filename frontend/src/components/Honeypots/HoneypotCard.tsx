import { Server, Activity, AlertTriangle, Trash2, Power } from 'lucide-react'
import { Honeypot } from '../../hooks/useApi'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

interface HoneypotCardProps {
  honeypot: Honeypot
  onDelete?: (id: string) => void
  onToggle?: (id: string) => void
}

function HoneypotCard({ honeypot, onDelete, onToggle }: HoneypotCardProps) {
  const statusColors = {
    active: 'badge-success',
    inactive: 'badge-info',
    error: 'badge-critical',
  }

  return (
    <div className="glass-card-glow p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-cyber-500/10 border border-cyber-500/20">
            <Server className="w-6 h-6 text-cyber-500" />
          </div>
          <div>
            <h3 className="font-semibold text-lg">{honeypot.name}</h3>
            <p className="text-sm text-slate-500 font-mono">{honeypot.id.slice(0, 8)}...</p>
          </div>
        </div>
        <span className={clsx('badge', statusColors[honeypot.status] || 'badge-info')}>
          {honeypot.status}
        </span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-4 mb-5 p-4 bg-dark-800/30 rounded-xl">
        <div className="text-center">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Type</p>
          <p className="font-semibold text-cyber-400 mt-1">{honeypot.type.toUpperCase()}</p>
        </div>
        <div className="text-center border-x border-dark-700">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Port</p>
          <p className="font-semibold mt-1">{honeypot.port}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Health</p>
          <p className="font-semibold mt-1">{honeypot.health}%</p>
        </div>
      </div>

      {/* Activity */}
      <div className="flex items-center gap-6 text-sm text-slate-400 mb-5">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          <span>{honeypot.attacks_detected} attacks</span>
        </div>
        {honeypot.last_activity && (
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyber-500" />
            <span>{formatDistanceToNow(new Date(honeypot.last_activity))} ago</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        {onToggle && (
          <button
            onClick={() => onToggle(honeypot.id)}
            className="btn-secondary flex-1"
          >
            {honeypot.status === 'active' ? (
              <>
                <Power className="w-4 h-4" />
                Stop
              </>
            ) : (
              <>
                <Power className="w-4 h-4" />
                Start
              </>
            )}
          </button>
        )}
        {onDelete && (
          <button
            onClick={() => onDelete(honeypot.id)}
            className="btn-danger flex-1"
          >
            <Trash2 className="w-4 h-4" />
            Remove
          </button>
        )}
      </div>
    </div>
  )
}

export default HoneypotCard