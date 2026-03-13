import { useMemo } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions,
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import { DashboardStats } from '../../hooks/useApi'
import { format, parseISO } from 'date-fns'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface AttackChartProps {
  stats: DashboardStats | undefined
  isLoading: boolean
}

const chartColors = {
  cyber: {
    border: 'rgb(20, 184, 166)',
    background: 'rgba(20, 184, 166, 0.1)',
  },
  red: {
    border: 'rgb(239, 68, 68)',
    background: 'rgba(239, 68, 68, 0.1)',
  },
  yellow: {
    border: 'rgb(234, 179, 8)',
    background: 'rgba(234, 179, 8, 0.1)',
  },
  blue: {
    border: 'rgb(59, 130, 246)',
    background: 'rgba(59, 130, 246, 0.1)',
  },
}

const commonOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      titleColor: 'rgb(226, 232, 240)',
      bodyColor: 'rgb(148, 163, 184)',
      borderColor: 'rgba(51, 65, 85, 0.5)',
      borderWidth: 1,
      padding: 12,
      displayColors: false,
    },
  },
  scales: {
    x: {
      grid: {
        color: 'rgba(51, 65, 85, 0.3)',
        drawBorder: false,
      },
      ticks: {
        color: 'rgb(100, 116, 139)',
      },
    },
    y: {
      grid: {
        color: 'rgba(51, 65, 85, 0.3)',
        drawBorder: false,
      },
      ticks: {
        color: 'rgb(100, 116, 139)',
      },
      beginAtZero: true,
    },
  },
  interaction: {
    intersect: false,
    mode: 'index',
  },
} as const

function AttackTimelineChart({ stats, isLoading }: AttackChartProps) {
  const data = useMemo(() => {
    if (!stats?.attack_timeline) {
      return {
        labels: [],
        datasets: [],
      }
    }

    return {
      labels: stats.attack_timeline.map((item) => {
        try {
          return format(parseISO(item.time), 'HH:mm')
        } catch {
          return item.time
        }
      }),
      datasets: [
        {
          label: 'Attacks',
          data: stats.attack_timeline.map((item) => item.count),
          borderColor: chartColors.cyber.border,
          backgroundColor: chartColors.cyber.background,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHoverBackgroundColor: chartColors.cyber.border,
        },
      ],
    }
  }, [stats])

  if (isLoading) {
    return (
      <div className="card h-64">
        <div className="animate-pulse space-y-4">
          <div className="h-4 w-32 bg-dark-700 rounded" />
          <div className="h-full w-full bg-dark-700 rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="card h-64">
      <h3 className="text-lg font-semibold text-dark-100 mb-4">Attack Timeline</h3>
      <div className="h-44">
        <Line data={data} options={commonOptions} />
      </div>
    </div>
  )
}

function AttackTypeChart({ stats, isLoading }: AttackChartProps) {
  const data = useMemo(() => {
    if (!stats?.attacks_by_type) {
      return {
        labels: [],
        datasets: [],
      }
    }

    const colors = [
      'rgb(20, 184, 166)',
      'rgb(59, 130, 246)',
      'rgb(234, 179, 8)',
      'rgb(239, 68, 68)',
      'rgb(168, 85, 247)',
    ]

    const entries = Object.entries(stats.attacks_by_type)

    return {
      labels: entries.map(([type]) => type.toUpperCase()),
      datasets: [
        {
          label: 'Attacks',
          data: entries.map(([, count]) => count),
          backgroundColor: colors.slice(0, entries.length),
          borderRadius: 4,
        },
      ],
    }
  }, [stats])

  const barOptions: ChartOptions<'bar'> = {
    ...commonOptions,
    plugins: {
      ...commonOptions.plugins,
      legend: {
        display: false,
      },
    },
  }

  if (isLoading) {
    return (
      <div className="card h-64">
        <div className="animate-pulse space-y-4">
          <div className="h-4 w-32 bg-dark-700 rounded" />
          <div className="h-full w-full bg-dark-700 rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="card h-64">
      <h3 className="text-lg font-semibold text-dark-100 mb-4">Attacks by Type</h3>
      <div className="h-44">
        <Bar data={data} options={barOptions} />
      </div>
    </div>
  )
}

function SeverityChart({ stats, isLoading }: AttackChartProps) {
  const data = useMemo(() => {
    if (!stats?.attacks_by_severity) {
      return {
        labels: [],
        datasets: [],
      }
    }

    const severityColors: Record<string, string> = {
      critical: 'rgb(239, 68, 68)',
      high: 'rgb(249, 115, 22)',
      medium: 'rgb(234, 179, 8)',
      low: 'rgb(34, 197, 94)',
      info: 'rgb(59, 130, 246)',
    }

    const entries = Object.entries(stats.attacks_by_severity)

    return {
      labels: entries.map(([severity]) => severity.charAt(0).toUpperCase() + severity.slice(1)),
      datasets: [
        {
          label: 'Count',
          data: entries.map(([, count]) => count),
          backgroundColor: entries.map(([severity]) => severityColors[severity] || 'rgb(100, 116, 139)'),
          borderRadius: 4,
        },
      ],
    }
  }, [stats])

  const barOptions: ChartOptions<'bar'> = {
    ...commonOptions,
    indexAxis: 'y',
  }

  if (isLoading) {
    return (
      <div className="card h-64">
        <div className="animate-pulse space-y-4">
          <div className="h-4 w-32 bg-dark-700 rounded" />
          <div className="h-full w-full bg-dark-700 rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="card h-64">
      <h3 className="text-lg font-semibold text-dark-100 mb-4">Attacks by Severity</h3>
      <div className="h-44">
        <Bar data={data} options={barOptions} />
      </div>
    </div>
  )
}

function TopAttackersChart({ stats, isLoading }: AttackChartProps) {
  if (isLoading) {
    return (
      <div className="card h-64">
        <div className="animate-pulse space-y-4">
          <div className="h-4 w-32 bg-dark-700 rounded" />
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-8 bg-dark-700 rounded" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="card h-64">
      <h3 className="text-lg font-semibold text-dark-100 mb-4">Top Attackers</h3>
      <div className="space-y-3">
        {stats?.top_attackers?.slice(0, 5).map((attacker, index) => (
          <div key={attacker.ip} className="flex items-center gap-3">
            <span className="text-sm font-mono text-dark-400 w-6">#{index + 1}</span>
            <span className="flex-1 font-mono text-sm text-dark-200">{attacker.ip}</span>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2 bg-dark-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-cyber-500 rounded-full"
                  style={{
                    width: `${Math.min(
                      100,
                      (attacker.count / (stats.top_attackers[0]?.count || 1)) * 100
                    )}%`,
                  }}
                />
              </div>
              <span className="text-sm text-dark-300 w-12 text-right">{attacker.count}</span>
            </div>
          </div>
        ))}
        {(!stats?.top_attackers || stats.top_attackers.length === 0) && (
          <p className="text-sm text-dark-400 text-center py-8">No attackers detected</p>
        )}
      </div>
    </div>
  )
}

export { AttackTimelineChart, AttackTypeChart, SeverityChart, TopAttackersChart }
export default AttackTimelineChart