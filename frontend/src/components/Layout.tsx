import { ReactNode, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Shield, Activity, Server, AlertTriangle, Settings, Menu,
  Wifi, WifiOff, LogOut, ChevronLeft, Brain, Target
} from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAuth } from '../contexts/AuthContext'
import { NotificationProvider, useNotifications } from '../contexts/NotificationContext'
import NotificationDropdown from '../components/Notifications/NotificationDropdown'
import ThemeToggle from '../components/ThemeToggle'
import { useAppStore, useThemeEffect } from '../stores/appStore'

interface LayoutProps {
  children: ReactNode
}

function LayoutContent({ children }: LayoutProps) {
  const location = useLocation()
  const { connected, lastMessage } = useWebSocket()
  const { logout } = useAuth()
  const { notifications, markRead, markAllRead, clear, clearAll, addNotification } = useNotifications()
  const { sidebarCollapsed, toggleSidebar, setConnectionStatus } = useAppStore()
  
  // Apply theme effect
  useThemeEffect()
  
  // Sync connection status to store
  useEffect(() => {
    setConnectionStatus(connected ? 'connected' : 'disconnected')
  }, [connected, setConnectionStatus])

  // Create notifications from WebSocket events
  useEffect(() => {
    if (!lastMessage) return
    
    const msg = lastMessage as Record<string, unknown>
    
    // New attack detected
    if (msg.type === 'new_attack' || msg.type === 'attack_detected') {
      const data = msg.data as Record<string, unknown> | undefined
      addNotification({
        type: 'attack',
        title: 'New Attack Detected',
        message: data?.attack_type ? `${String(data.attack_type).toUpperCase()} attack from ${String(data.source_ip || 'unknown')}` : 'Attack activity detected',
        severity: (data?.severity as 'low' | 'medium' | 'high' | 'critical') || 'medium',
        source_ip: data?.source_ip ? String(data.source_ip) : undefined,
        honeypot_id: data?.honeypot_id ? String(data.honeypot_id) : undefined
      })
    }
    
    // AI decision made
    if (msg.type === 'ai_decision') {
      const data = msg.data as Record<string, unknown> | undefined
      addNotification({
        type: 'ai_decision',
        title: 'AI Decision Executed',
        message: data?.action ? `Action: ${String(data.action)}` : 'AI has made a decision',
        severity: 'low'
      })
    }
    
    // Security alert
    if (msg.type === 'security_alert') {
      const data = msg.data as Record<string, unknown> | undefined
      addNotification({
        type: 'security',
        title: 'Security Alert',
        message: data?.message ? String(data.message) : 'Security event detected',
        severity: (data?.severity as 'low' | 'medium' | 'high' | 'critical') || 'high'
      })
    }
    
    // Execution completed
    if (msg.type === 'execution_complete') {
      const data = msg.data as Record<string, unknown> | undefined
      addNotification({
        type: 'system',
        title: 'Execution Complete',
        message: data?.action ? `${String(data.action)} executed successfully` : 'Action completed',
        severity: 'low'
      })
    }
  }, [lastMessage, addNotification])

  // Listen for test notification event
  useEffect(() => {
    const handleTestNotification = () => {
      addNotification({
        type: 'system',
        title: 'Test Notification',
        message: 'This is a test notification. The notification system is working correctly!',
        severity: 'low'
      })
    }

    window.addEventListener('test-notification', handleTestNotification)
    return () => window.removeEventListener('test-notification', handleTestNotification)
  }, [addNotification])

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Activity },
    { name: 'Honeypots', href: '/honeypots', icon: Server },
    { name: 'Attacks', href: '/attacks', icon: AlertTriangle },
    { name: 'AI Monitor', href: '/ai-monitor', icon: Brain },
    { name: 'Cognitive', href: '/cognitive', icon: Target },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]

  return (
    <div className="min-h-screen bg-[var(--bg-deep)] text-[var(--text-primary)] flex">
      {/* Background Grid */}
      <div className="fixed inset-0 bg-grid-pattern bg-grid opacity-20 pointer-events-none"></div>
      
      {/* Sidebar */}
      <aside 
        className={`
          ${sidebarCollapsed ? 'w-20' : 'w-64'} 
          bg-[var(--bg-elevated)]/80 backdrop-blur-xl border-r border-[var(--border-subtle)] 
          transition-all duration-300 ease-out-expo 
          flex flex-col relative z-20
        `}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-[var(--border-subtle)]">
          <Link to="/" className="flex items-center gap-3">
            <div className="p-2 bg-[var(--accent-primary)]/10 rounded-xl border border-[var(--accent-primary)]/20">
              <Shield className="w-6 h-6 text-[var(--accent-primary)]" />
            </div>
            {!sidebarCollapsed && (
              <div className="animate-fade-in">
                <span className="font-bold text-lg bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                  Honeypot
                </span>
              </div>
            )}
          </Link>
          <button 
            onClick={toggleSidebar}
            className="p-2 rounded-xl hover:bg-[var(--bg-surface)] transition-colors text-[var(--text-muted)] hover:text-white"
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed ? <Menu className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`
                  flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200
                  ${isActive 
                    ? 'nav-item-active' 
                    : 'nav-item'
                  }
                `}
                title={sidebarCollapsed ? item.name : undefined}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {!sidebarCollapsed && (
                  <span className="font-medium animate-fade-in">{item.name}</span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Bottom Section */}
        <div className="p-4 border-t border-[var(--border-subtle)] space-y-4">
          {/* Theme Toggle */}
          <div className="flex justify-center">
            <ThemeToggle />
          </div>
          
          {/* Connection Status */}
          <div className={`
            flex items-center gap-3 px-3 py-2 rounded-xl
            ${connected ? 'bg-emerald-500/5 text-emerald-400' : 'bg-red-500/5 text-red-400'}
          `}>
            {connected ? (
              <Wifi className="w-4 h-4" />
            ) : (
              <WifiOff className="w-4 h-4" />
            )}
            {!sidebarCollapsed && (
              <span className="text-sm font-medium animate-fade-in">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            )}
          </div>

          {/* Logout Button */}
          <button
            onClick={logout}
            className="nav-item w-full justify-center md:justify-start"
            title="Sign out"
          >
            <LogOut className="w-5 h-5" />
            {!sidebarCollapsed && <span className="animate-fade-in">Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden relative z-10">
        {/* Header */}
        <header className="h-16 bg-[var(--bg-elevated)]/60 backdrop-blur-xl border-b border-[var(--border-subtle)] flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold">
              {navigation.find(n => n.href === location.pathname)?.name || 'Dashboard'}
            </h1>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Connection indicator */}
            <div className={`
              flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium
              ${connected 
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                : 'bg-red-500/10 text-red-400 border border-red-500/20'
              }
            `}>
              <span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500 status-dot-success' : 'bg-red-500 status-dot-danger'}`}></span>
              {connected ? 'Live' : 'Offline'}
            </div>
            
            {/* Notifications */}
            <NotificationDropdown 
              notifications={notifications}
              onMarkRead={markRead}
              onMarkAllRead={markAllRead}
              onClear={clear}
              onClearAll={clearAll}
            />
            
            {/* User */}
            <div className="flex items-center gap-3 pl-3 border-l border-[var(--border-subtle)]">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[var(--accent-primary)]/20 to-purple-500/20 border border-[var(--border-subtle)] flex items-center justify-center">
                <span className="text-sm font-semibold text-[var(--accent-primary)]">A</span>
              </div>
              <div className="hidden md:block">
                <p className="text-sm font-medium">Admin</p>
                <p className="text-xs text-[var(--text-muted)]">Administrator</p>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">
          <div className="animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

export default function Layout({ children }: LayoutProps) {
  return (
    <NotificationProvider>
      <LayoutContent>{children}</LayoutContent>
    </NotificationProvider>
  )
}