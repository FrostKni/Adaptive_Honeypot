import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import { useToastStore, ToastType } from '../stores/toastStore'
import clsx from 'clsx'

const iconMap = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

const colorMap = {
  success: {
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    icon: 'text-emerald-400',
    title: 'text-emerald-300',
  },
  error: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    icon: 'text-red-400',
    title: 'text-red-300',
  },
  warning: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    icon: 'text-amber-400',
    title: 'text-amber-300',
  },
  info: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    icon: 'text-blue-400',
    title: 'text-blue-300',
  },
}

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md w-full pointer-events-none">
      {toasts.map((toast, index) => (
        <ToastItem 
          key={toast.id} 
          toast={toast} 
          onClose={() => removeToast(toast.id)}
          style={{ 
            animationDelay: `${index * 50}ms`,
            pointerEvents: 'auto'
          }}
        />
      ))}
    </div>
  )
}

interface ToastItemProps {
  toast: {
    id: string
    type: ToastType
    title: string
    message?: string
  }
  onClose: () => void
  style?: React.CSSProperties
}

function ToastItem({ toast, onClose, style }: ToastItemProps) {
  const Icon = iconMap[toast.type]
  const colors = colorMap[toast.type]

  return (
    <div
      className={clsx(
        'flex items-start gap-3 p-4 rounded-xl border backdrop-blur-xl animate-slide-in',
        colors.bg,
        colors.border
      )}
      style={style}
    >
      <Icon className={clsx('w-5 h-5 flex-shrink-0 mt-0.5', colors.icon)} />
      <div className="flex-1 min-w-0">
        <p className={clsx('font-medium text-sm', colors.title)}>
          {toast.title}
        </p>
        {toast.message && (
          <p className="text-sm text-slate-400 mt-0.5">{toast.message}</p>
        )}
      </div>
      <button
        onClick={onClose}
        className="p-1 rounded-lg hover:bg-white/10 transition-colors text-slate-400 hover:text-white"
        aria-label="Dismiss notification"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}
