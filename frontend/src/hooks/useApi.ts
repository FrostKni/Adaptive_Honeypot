import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getApiUrl } from '../config/env'
import { toast } from '../stores/toastStore'

// Helper to get auth token
function getAuthToken(): string | null {
  return localStorage.getItem('token')
}

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
  payload: string
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

export interface ApiError {
  detail: string
  status: number
}

async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token = getAuthToken()
  
  const response = await fetch(getApiUrl(`/api/v1${endpoint}`), {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error: ApiError = {
      detail: response.statusText,
      status: response.status,
    }
    try {
      const data = await response.json()
      error.detail = data.detail || response.statusText
    } catch {
      // Use status text if JSON parsing fails
    }
    throw error
  }

  return response.json()
}

// Query keys
export const queryKeys = {
  honeypots: ['honeypots'] as const,
  honeypot: (id: string) => ['honeypots', id] as const,
  sessions: ['sessions'] as const,
  session: (id: string) => ['sessions', id] as const,
  attacks: ['attacks'] as const,
  attack: (id: string) => ['attacks', id] as const,
  dashboardStats: ['dashboard', 'stats'] as const,
}

// Honeypots
export function useHoneypots() {
  return useQuery<Honeypot[]>({
    queryKey: queryKeys.honeypots,
    queryFn: () => apiRequest<Honeypot[]>('/honeypots'),
    // Removed aggressive auto-refresh - use WebSocket for real-time updates instead
    // Manual refresh via UI button or invalidate on WebSocket events
  })
}

export function useHoneypot(id: string) {
  return useQuery<Honeypot>({
    queryKey: queryKeys.honeypot(id),
    queryFn: () => apiRequest<Honeypot>(`/honeypots/${id}`),
    enabled: !!id,
  })
}

export function useCreateHoneypot() {
  const queryClient = useQueryClient()
  
  return useMutation<Honeypot, ApiError, CreateHoneypotRequest>({
    mutationFn: (data) =>
      apiRequest<Honeypot>('/honeypots', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.honeypots })
      toast.success('Honeypot Created', `${data.name} is now being deployed`)
    },
  })
}

export function useDeleteHoneypot() {
  const queryClient = useQueryClient()
  
  return useMutation<void, ApiError, string>({
    mutationFn: (id) =>
      apiRequest(`/honeypots/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.honeypots })
      toast.success('Honeypot Removed', 'The honeypot has been deleted')
    },
  })
}

// Sessions
export function useSessions(params?: { honeypot_id?: string; limit?: number }) {
  const searchParams = new URLSearchParams()
  if (params?.honeypot_id) searchParams.set('honeypot_id', params.honeypot_id)
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  
  const queryString = searchParams.toString()
  
  return useQuery<Session[]>({
    queryKey: [...queryKeys.sessions, params],
    queryFn: async () => {
      const result = await apiRequest<{ items: Session[], total: number }>(`/sessions${queryString ? `?${queryString}` : ''}`)
      return result.items || []
    },
  })
}

export function useSession(id: string) {
  return useQuery<Session>({
    queryKey: queryKeys.session(id),
    queryFn: () => apiRequest<Session>(`/sessions/${id}`),
    enabled: !!id,
  })
}

// Attacks
export function useAttacks(params?: { honeypot_id?: string; severity?: string; limit?: number }) {
  const searchParams = new URLSearchParams()
  if (params?.honeypot_id) searchParams.set('honeypot_id', params.honeypot_id)
  if (params?.severity) searchParams.set('severity', params.severity)
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  
  const queryString = searchParams.toString()
  
  return useQuery<AttackEvent[]>({
    queryKey: [...queryKeys.attacks, params],
    queryFn: async () => {
      const result = await apiRequest<{ items: AttackEvent[], total: number }>(`/attacks${queryString ? `?${queryString}` : ''}`)
      return result.items || []
    },
  })
}

export function useAttack(id: string) {
  return useQuery<AttackEvent>({
    queryKey: queryKeys.attack(id),
    queryFn: () => apiRequest<AttackEvent>(`/attacks/${id}`),
    enabled: !!id,
  })
}

// Dashboard
export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: queryKeys.dashboardStats,
    queryFn: () => apiRequest<DashboardStats>('/analytics/dashboard'),
    // Reduced from 10s to 30s - WebSocket provides real-time updates
    refetchInterval: 30000,
  })
}

// Settings types
export interface AIProviderConfig {
  enabled: boolean
  apiKey: string
  baseUrl: string
  model: string
}

export interface AIConfigSettings {
  activeProvider: string
  local: AIProviderConfig
  openai: AIProviderConfig
  anthropic: AIProviderConfig
  gemini: AIProviderConfig
  analysisEnabled: boolean
  autoAnalyze: boolean
  analysisInterval: number
  threatThreshold: number
}

export interface UserSettings {
  notifications: {
    emailAlerts: boolean
    criticalAlerts: boolean
    dailyDigest: boolean
    slackWebhook: string
  }
  security: {
    autoAdaptation: boolean
    maxHoneypots: number
    sessionTimeout: number
    blockMaliciousIPs: boolean
  }
  display: {
    theme: string
    compactView: boolean
    autoRefresh: boolean
    refreshInterval: number
  }
  api: {
    apiKey: string
    apiEndpoint: string
    wsEndpoint: string
  }
  ai: AIConfigSettings
}

export interface SystemStatus {
  apiServer: string
  database: string
  websocket: string
  honeypotContainers: number
  cpuPercent: number
  memoryPercent: number
  diskPercent: number
  uptime: string
}

// Settings hooks
export function useSettings() {
  return useQuery<UserSettings>({
    queryKey: ['settings'],
    queryFn: () => apiRequest<UserSettings>('/settings'),
  })
}

export function useUpdateSettings() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (settings: UserSettings) => 
      apiRequest<UserSettings>('/settings', {
        method: 'PUT',
        body: JSON.stringify(settings),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
    },
  })
}

export function useSystemStatus() {
  return useQuery<SystemStatus>({
    queryKey: ['systemStatus'],
    queryFn: () => apiRequest<SystemStatus>('/settings/status'),
    // Reduced from 5s to 30s - system status doesn't change frequently
    refetchInterval: 30000,
  })
}

export function useResetSettings() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => 
      apiRequest<UserSettings>('/settings/reset', {
        method: 'POST',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
    },
  })
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (data: { currentPassword: string; newPassword: string }) =>
      apiRequest<{ success: boolean; message: string }>('/settings/change-password', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

export function useTestWebhook() {
  return useMutation({
    mutationFn: (webhookUrl: string) =>
      apiRequest<{ success: boolean; message: string }>(`/settings/test-webhook?webhook_url=${encodeURIComponent(webhookUrl)}`, {
        method: 'POST',
      }),
  })
}

export function useTestAIProvider() {
  return useMutation({
    mutationFn: (provider: string) =>
      apiRequest<{ success: boolean; message: string }>(`/settings/test-ai-provider?provider=${encodeURIComponent(provider)}`, {
        method: 'POST',
      }),
  })
}

// Utility to invalidate all queries (useful after WebSocket updates)
export function useInvalidateQueries() {
  const queryClient = useQueryClient()
  
  return () => {
    queryClient.invalidateQueries()
  }
}