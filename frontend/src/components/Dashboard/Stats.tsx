import { TrendingUp, TrendingDown, Server, Shield, Activity, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'
import { DashboardStats } from '../../hooks/useApi'

interface StatsProps {
  stats: DashboardStats | undefined
  isLoading: boolean
}

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: number
  trendLabel?: string
  color: 'cyber' | 'red' | 'yellow' | 'blue'
  isLoading?: boolean
}

function StatCard({ title, value, icon, trend, trendLabel, color, isLoading }: StatCardProps) {
  const colorClasses = {
    cyber: 'from-cyber-500/20 to-cyber-500/5 text-cyber-400',
    red: 'from-red-500/20 to-red-500/5 text-red-400',
    yellow: 'from-yellow-500/20 to-yellow-500/5 text-yellow-400',
    blue: 'from-blue-500/20 to-blue-500/5 text-blue-400',
  }

  if (isLoading) {
    return (
      <div className="stat-card">
        <div className="flex items-start justify-between">
          <div className="space-y-3">
            <div className="h-4 w-24 bg-dark-700 rounded animate-pulse" />
            <div className="h-8 w-20 bg-dark-700 rounded animate-pulse" />
          </div>
          <div className="w-12 h-12 bg-dark-700 rounded-lg animate-pulse" />
        </div>
      </div>
    )
  }

  return (
    <div className="stat-card group">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-dark-400">{title}</p>
          <p className="mt-2 text-3xl font-bold text-dark-100">{value.toLocaleString()}</p>
          
          {trend !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              {trend >= 0 ? (
                <TrendingUp className="w-4 h-4 text-green-400" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-400" />
              )}
              <span
                className={clsx(
                  'text-sm font-medium',
                  trend >= 0 ? 'text-green-400' : 'text-red-400'
                )}
              >
                {Math.abs(trend)}%
              </span>
              {trendLabel && (
                <span className="text-sm text-dark-400">{trendLabel}</span>
              )}
            </div>
          )}
        </div>

        <div
          className={clsx(
            'p-3 rounded-lg bg-gradient-to-br',
            colorClasses[color]
          )}
        >
          {icon}
        </div>
      </div>
    </div>
  )
}

function Stats({ stats, isLoading }: StatsProps) {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        title="Total Attacks"
        value={stats?.total_attacks ?? 0}
        icon={<Shield className="w-6 h-6" />}
        color="red"
        trend={12}
        trendLabel="vs last week"
        isLoading={isLoading}
      />
      
      <StatCard
        title="Active Honeypots"
        value={stats?.active_honeypots ?? 0}
        icon={<Server className="w-6 h-6" />}
        color="cyber"
        isLoading={isLoading}
      />
      
      <StatCard
        title="Active Sessions"
        value={stats?.active_sessions ?? 0}
        icon={<Activity className="w-6 h-6" />}
        color="blue"
        isLoading={isLoading}
      />
      
      <StatCard
        title="Attacks Today"
        value={stats?.attacks_today ?? 0}
        icon={<AlertTriangle className="w-6 h-6" />}
        color="yellow"
        trend={-8}
        trendLabel="vs yesterday"
        isLoading={isLoading}
      />
    </div>
  )
}

export default Stats