// Type definitions for the Adaptive Honeypot Dashboard

export interface Honeypot {
  id: string
  name: string
  type: string
  protocol: string
  port: number
  status: 'active' | 'inactive' | 'error'
  health: number
  attacks_detected: number
  created_at: string
  last_activity: string | null
  config: Record<string, unknown>
}

export interface Session {
  id: string
  honeypot_id: string
  source_ip: string
  source_port: number
  protocol: string
  started_at: string
  ended_at: string | null
  duration: number | null
  commands: SessionCommand[]
  bytes_sent: number
  bytes_received: number
}

export interface SessionCommand {
  timestamp: string
  command: string
  response?: string
}

export interface AttackEvent {
  id: string
  honeypot_id: string
  honeypot_name: string
  type: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  source_ip: string
  source_port: number
  protocol: string
  payload: string | Record<string, unknown>
  timestamp: string
  session_id: string | null
  metadata: Record<string, unknown>
}

export interface DashboardStats {
  total_attacks: number
  active_honeypots: number
  active_sessions: number
  attacks_today: number
  attacks_by_type: Record<string, number>
  attacks_by_severity: Record<string, number>
  top_attackers: Array<{ ip: string; count: number }>
  attack_timeline: Array<{ time: string; count: number }>
  honeypot_health: Array<{ id: string; name: string; health: number }>
}

export interface CreateHoneypotRequest {
  name: string
  type: string
  protocol: string
  port: number
  config?: Record<string, unknown>
}

export type WebSocketMessageType = 'attack_event' | 'adaptation' | 'alert' | 'honeypot_status'

export interface WebSocketMessage {
  type: WebSocketMessageType
  data: unknown
  timestamp: string
}

export interface ApiError {
  detail: string
  status: number
}

// Component Props
export interface HoneypotCardProps {
  honeypot: Honeypot
  onDelete?: (id: string) => void
  onToggle?: (id: string) => void
}

export interface AttackFeedProps {
  initialAttacks?: AttackEvent[]
  maxItems?: number
}

export interface SessionReplayProps {
  session: Session | null
  isLoading?: boolean
}

export interface StatsProps {
  stats: DashboardStats | undefined
  isLoading: boolean
}

export interface AttackChartProps {
  stats: DashboardStats | undefined
  isLoading: boolean
}

export interface AttackLocation {
  ip: string
  lat: number
  lng: number
  country: string
  city?: string
  attack_count: number
  last_attack: string
  attack_types: string[]
  severity: 'low' | 'medium' | 'high' | 'critical'
}

export interface AttackMapProps {
  attacks: AttackLocation[]
  onLocationClick?: (location: AttackLocation) => void
  refreshInterval?: number
}