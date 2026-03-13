import { useState } from 'react'
import { Plus, Search, Filter, RefreshCw } from 'lucide-react'
import { useHoneypots, useCreateHoneypot, Honeypot } from '../../hooks/useApi'
import HoneypotCard from './HoneypotCard'
import clsx from 'clsx'

const HONEYPOT_TYPES = [
  { value: 'ssh', label: 'SSH Honeypot' },
  { value: 'http', label: 'HTTP Honeypot' },
  { value: 'ftp', label: 'FTP Honeypot' },
  { value: 'telnet', label: 'Telnet Honeypot' },
  { value: 'mysql', label: 'MySQL Honeypot' },
  { value: 'redis', label: 'Redis Honeypot' },
]

const PROTOCOLS = ['TCP', 'UDP']

function HoneypotList() {
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newHoneypot, setNewHoneypot] = useState({
    name: '',
    type: 'ssh',
    protocol: 'TCP',
    port: 2222,
  })

  const { data: honeypots, isLoading, refetch, isRefetching } = useHoneypots()
  const createMutation = useCreateHoneypot()

  const filteredHoneypots = honeypots?.filter((hp: Honeypot) => {
    const matchesSearch =
      hp.name.toLowerCase().includes(search.toLowerCase()) ||
      hp.type.toLowerCase().includes(search.toLowerCase())
    const matchesStatus = filterStatus === 'all' || hp.status === filterStatus
    return matchesSearch && matchesStatus
  })

  const handleCreate = async () => {
    if (!newHoneypot.name.trim()) return

    await createMutation.mutateAsync({
      name: newHoneypot.name,
      type: newHoneypot.type,
      protocol: newHoneypot.protocol,
      port: newHoneypot.port,
    })

    setShowCreateModal(false)
    setNewHoneypot({ name: '', type: 'ssh', protocol: 'TCP', port: 2222 })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="flex items-center gap-3">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
            <input
              type="text"
              placeholder="Search honeypots..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>

          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input pl-10 pr-8 appearance-none cursor-pointer"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="error">Error</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={clsx('w-4 h-4', isRefetching && 'animate-spin')} />
            Refresh
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Honeypot
          </button>
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card h-48 animate-pulse">
              <div className="h-full w-full bg-dark-700 rounded" />
            </div>
          ))}
        </div>
      ) : filteredHoneypots && filteredHoneypots.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredHoneypots.map((honeypot: Honeypot) => (
            <HoneypotCard key={honeypot.id} honeypot={honeypot} />
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-dark-400">No honeypots found</p>
          {search && (
            <p className="text-sm text-dark-500 mt-2">
              Try adjusting your search or filter
            </p>
          )}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-dark-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md card">
            <h3 className="text-lg font-semibold text-dark-100 mb-6">Create New Honeypot</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  Name
                </label>
                <input
                  type="text"
                  value={newHoneypot.name}
                  onChange={(e) =>
                    setNewHoneypot({ ...newHoneypot, name: e.target.value })
                  }
                  placeholder="my-honeypot"
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  Type
                </label>
                <select
                  value={newHoneypot.type}
                  onChange={(e) =>
                    setNewHoneypot({ ...newHoneypot, type: e.target.value })
                  }
                  className="input"
                >
                  {HONEYPOT_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    Protocol
                  </label>
                  <select
                    value={newHoneypot.protocol}
                    onChange={(e) =>
                      setNewHoneypot({ ...newHoneypot, protocol: e.target.value })
                    }
                    className="input"
                  >
                    {PROTOCOLS.map((protocol) => (
                      <option key={protocol} value={protocol}>
                        {protocol}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    Port
                  </label>
                  <input
                    type="number"
                    value={newHoneypot.port}
                    onChange={(e) =>
                      setNewHoneypot({
                        ...newHoneypot,
                        port: parseInt(e.target.value) || 0,
                      })
                    }
                    className="input"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={createMutation.isPending || !newHoneypot.name.trim()}
                className="btn-primary"
              >
                {createMutation.isPending ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default HoneypotList