import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Plus, Trash2, Server, Activity, AlertTriangle, Play, Square, RefreshCw, X } from 'lucide-react'

interface Honeypot {
  id: string
  name: string
  type: string
  port: number
  status: string
  interaction_level: string
  total_sessions: number
  total_attacks: number
  created_at: string
}

export default function Honeypots() {
  const [showDeploy, setShowDeploy] = useState(false)
  const [deployForm, setDeployForm] = useState({
    name: 'ssh-honeypot',
    type: 'ssh',
    port: 2222,
  })
  const queryClient = useQueryClient()

  const { data: honeypots, isLoading } = useQuery<{ items: Honeypot[], total: number }>({
    queryKey: ['honeypots'],
    queryFn: async () => {
      const res = await fetch('/api/v1/honeypots', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      if (!res.ok) throw new Error('Failed to fetch honeypots')
      return res.json()
    },
  })

  const deployMutation = useMutation({
    mutationFn: async (data: typeof deployForm) => {
      const res = await fetch('/api/v1/honeypots', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('Failed to deploy')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['honeypots'] })
      setShowDeploy(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`/api/v1/honeypots/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      if (!res.ok) throw new Error('Failed to delete')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['honeypots'] })
    },
  })

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
            Honeypots
          </h2>
          <p className="text-slate-500 mt-1">Manage your honeypot fleet</p>
        </div>
        <button
          onClick={() => setShowDeploy(true)}
          className="btn-primary"
        >
          <Plus className="w-4 h-4" />
          Deploy Honeypot
        </button>
      </div>

      {/* Deploy Modal */}
      {showDeploy && (
        <div className="modal-overlay" onClick={() => setShowDeploy(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">Deploy New Honeypot</h3>
              <button 
                onClick={() => setShowDeploy(false)}
                className="p-2 rounded-xl hover:bg-dark-800 transition-colors text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-5">
              <div>
                <label className="input-label">Name</label>
                <input
                  type="text"
                  value={deployForm.name}
                  onChange={(e) => setDeployForm({ ...deployForm, name: e.target.value })}
                  className="input"
                  placeholder="e.g., ssh-honeypot-1"
                />
              </div>
              
              <div>
                <label className="input-label">Type</label>
                <select
                  value={deployForm.type}
                  onChange={(e) => setDeployForm({ ...deployForm, type: e.target.value })}
                  className="select"
                >
                  <option value="ssh">SSH</option>
                  <option value="http">HTTP</option>
                  <option value="ftp">FTP</option>
                </select>
              </div>
              
              <div>
                <label className="input-label">Port</label>
                <input
                  type="number"
                  value={deployForm.port}
                  onChange={(e) => setDeployForm({ ...deployForm, port: parseInt(e.target.value) })}
                  className="input"
                  placeholder="2222"
                />
              </div>
            </div>
            
            <div className="flex gap-3 mt-8">
              <button
                onClick={() => setShowDeploy(false)}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
              <button
                onClick={() => deployMutation.mutate(deployForm)}
                disabled={deployMutation.isPending}
                className="btn-primary flex-1"
              >
                {deployMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Deploying...
                  </span>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Deploy
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Honeypots Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-4">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-dark-800 rounded-full"></div>
              <div className="absolute top-0 left-0 w-16 h-16 border-4 border-cyber-500 rounded-full border-t-transparent animate-spin"></div>
            </div>
            <p className="text-slate-500">Loading honeypots...</p>
          </div>
        </div>
      ) : honeypots?.items.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-dark-800/50 flex items-center justify-center">
            <Server className="w-10 h-10 text-slate-600" />
          </div>
          <h3 className="text-xl font-semibold mb-2">No Honeypots Deployed</h3>
          <p className="text-slate-500 mb-8 max-w-md mx-auto">
            Deploy your first honeypot to start monitoring attacks and collecting threat intelligence.
          </p>
          <button
            onClick={() => setShowDeploy(true)}
            className="btn-primary"
          >
            <Plus className="w-4 h-4" />
            Deploy Your First Honeypot
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {honeypots?.items.map((hp, index) => (
            <HoneypotCard 
              key={hp.id} 
              honeypot={hp} 
              onDelete={() => deleteMutation.mutate(hp.id)}
              isDeleting={deleteMutation.isPending}
              style={{ animationDelay: `${index * 50}ms` }}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// Honeypot Card Component
function HoneypotCard({ 
  honeypot, 
  onDelete, 
  isDeleting,
  style 
}: { 
  honeypot: Honeypot
  onDelete: () => void
  isDeleting: boolean
  style?: React.CSSProperties
}) {
  const statusConfig = {
    running: { color: 'badge-success', icon: Play },
    stopped: { color: 'badge-info', icon: Square },
    error: { color: 'badge-critical', icon: AlertTriangle },
    starting: { color: 'badge-medium', icon: RefreshCw },
  }
  
  const config = statusConfig[honeypot.status as keyof typeof statusConfig] || statusConfig.stopped
  const StatusIcon = config.icon

  return (
    <div className="glass-card-glow p-6 animate-fade-in" style={style}>
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
        <span className={`badge ${config.color} flex items-center gap-1.5`}>
          <StatusIcon className="w-3 h-3" />
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
          <p className="text-xs text-slate-500 uppercase tracking-wide">Level</p>
          <p className="font-semibold mt-1 capitalize">{honeypot.interaction_level}</p>
        </div>
      </div>

      {/* Activity */}
      <div className="flex items-center gap-6 text-sm text-slate-400 mb-5">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyber-500" />
          <span>{honeypot.total_sessions} sessions</span>
        </div>
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          <span>{honeypot.total_attacks} attacks</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={onDelete}
          disabled={isDeleting}
          className="btn-danger flex-1"
        >
          <Trash2 className="w-4 h-4" />
          {isDeleting ? 'Removing...' : 'Remove'}
        </button>
      </div>
    </div>
  )
}