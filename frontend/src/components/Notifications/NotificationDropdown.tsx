import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { Bell, AlertTriangle, Shield, Activity, Check, Trash2 } from 'lucide-react'

export interface Notification {
  id: string
  type: 'attack' | 'system' | 'ai_decision' | 'security'
  title: string
  message: string
  timestamp: string
  read: boolean
  severity?: 'low' | 'medium' | 'high' | 'critical'
  source_ip?: string
  honeypot_id?: string
}

interface NotificationDropdownProps {
  notifications: Notification[]
  onMarkRead: (id: string) => void
  onMarkAllRead: () => void
  onClear: (id: string) => void
  onClearAll: () => void
}

export default function NotificationDropdown({
  notifications,
  onMarkRead,
  onMarkAllRead,
  onClear,
  onClearAll
}: NotificationDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [position, setPosition] = useState({ top: 0, right: 0 })
  const buttonRef = useRef<HTMLButtonElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const unreadCount = notifications.filter(n => !n.read).length

  // Update position when opening
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      setPosition({
        top: rect.bottom + 8,
        right: window.innerWidth - rect.right
      })
    }
  }, [isOpen])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current && 
        !dropdownRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  // Close on escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
    }
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen])

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'attack':
        return <AlertTriangle className="w-4 h-4 text-red-400" />
      case 'ai_decision':
        return <Shield className="w-4 h-4 text-purple-400" />
      case 'security':
        return <Shield className="w-4 h-4 text-amber-400" />
      default:
        return <Activity className="w-4 h-4 text-cyan-400" />
    }
  }

  const getSeverityColor = (severity?: Notification['severity']) => {
    switch (severity) {
      case 'critical':
        return 'border-l-red-500 bg-red-500/5'
      case 'high':
        return 'border-l-orange-500 bg-orange-500/5'
      case 'medium':
        return 'border-l-amber-500 bg-amber-500/5'
      case 'low':
        return 'border-l-green-500 bg-green-500/5'
      default:
        return 'border-l-slate-500 bg-slate-500/5'
    }
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    return date.toLocaleDateString()
  }

  const dropdownContent = isOpen && (
    <div 
      ref={dropdownRef}
      className="fixed bg-dark-900/95 backdrop-blur-xl border border-dark-700 rounded-xl shadow-2xl overflow-hidden animate-scale-in"
      style={{ 
        top: position.top, 
        right: position.right,
        width: 'min(384px, calc(100vw - 32px))',
        zIndex: 9999
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-dark-700 bg-dark-800/50">
        <h3 className="font-semibold text-white">Notifications</h3>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <button
              onClick={onMarkAllRead}
              className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              Mark all read
            </button>
          )}
          {notifications.length > 0 && (
            <button
              onClick={onClearAll}
              className="text-xs text-slate-400 hover:text-red-400 transition-colors"
            >
              Clear all
            </button>
          )}
        </div>
      </div>

      {/* Notification List */}
      <div className="max-h-[400px] overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-slate-500">
            <Bell className="w-10 h-10 mb-3 opacity-30" />
            <p className="text-sm">No notifications</p>
            <p className="text-xs text-slate-600 mt-1">You're all caught up!</p>
          </div>
        ) : (
          <div className="divide-y divide-dark-800">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`
                  relative px-4 py-3 border-l-2 transition-colors hover:bg-dark-800/50
                  ${getSeverityColor(notification.severity)}
                  ${!notification.read ? 'bg-dark-800/30' : ''}
                `}
              >
                <div className="flex items-start gap-3">
                  {/* Icon */}
                  <div className="flex-shrink-0 mt-0.5">
                    {getIcon(notification.type)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className={`text-sm font-medium ${!notification.read ? 'text-white' : 'text-slate-300'}`}>
                        {notification.title}
                      </p>
                      <span className="text-xs text-slate-500 flex-shrink-0">
                        {formatTime(notification.timestamp)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">
                      {notification.message}
                    </p>
                    {notification.source_ip && (
                      <p className="text-xs text-cyan-500/70 mt-1 font-mono">
                        {notification.source_ip}
                      </p>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 mt-2 ml-7">
                  {!notification.read && (
                    <button
                      onClick={() => onMarkRead(notification.id)}
                      className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
                    >
                      <Check className="w-3 h-3" />
                      Mark read
                    </button>
                  )}
                  <button
                    onClick={() => onClear(notification.id)}
                    className="flex items-center gap-1 text-xs text-slate-400 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                    Dismiss
                  </button>
                </div>

                {/* Unread indicator */}
                {!notification.read && (
                  <div className="absolute top-3 right-3 w-2 h-2 bg-cyan-400 rounded-full"></div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {notifications.length > 0 && (
        <div className="px-4 py-2 border-t border-dark-700 bg-dark-800/30">
          <p className="text-xs text-slate-500 text-center">
            {unreadCount} unread · {notifications.length} total
          </p>
        </div>
      )}
    </div>
  )

  return (
    <>
      {/* Bell Button */}
      <button 
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="btn-ghost p-2 rounded-xl relative hover:bg-dark-800 transition-colors"
        aria-label="Notifications"
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-red-500 rounded-full flex items-center justify-center text-[10px] font-bold text-white border-2 border-dark-900">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Portal for dropdown - renders at document body level */}
      {typeof window !== 'undefined' && dropdownContent && createPortal(dropdownContent, document.body)}
    </>
  )
}