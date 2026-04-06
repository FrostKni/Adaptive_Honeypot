/**
 * Environment Configuration
 * 
 * Centralized configuration using environment variables.
 * Falls back to defaults if not provided.
 */

interface Config {
  apiUrl: string
  wsUrl: string
  appName: string
  appVersion: string
}

export const config: Config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  appName: import.meta.env.VITE_APP_NAME || 'Adaptive Honeypot',
  appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',
}

// Helper to get full API URL
export function getApiUrl(path: string = ''): string {
  return `${config.apiUrl}${path.startsWith('/') ? path : `/${path}`}`
}

// Helper to get WebSocket URL
export function getWsUrl(path: string = ''): string {
  return `${config.wsUrl}${path.startsWith('/') ? path : `/${path}`}`
}
