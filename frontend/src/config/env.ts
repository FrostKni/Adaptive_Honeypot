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

// CRITICAL: These values are evaluated at BUILD time by Vite
// To make them work with the Vite proxy, we need to:
// 1. Set VITE_API_URL="" in .env or during build
// 2. OR use window.location to get the current host at runtime

// For development: Use empty string so requests go through Vite proxy
// For production: Set VITE_API_URL to your backend URL
const resolveApiUrl = (): string => {
  // Check for environment variable (build-time)
  const envUrl = import.meta.env.VITE_API_URL
  if (envUrl !== undefined && envUrl !== '') {
    return envUrl
  }
  
  // Runtime: Use current host (goes through Vite proxy in dev)
  // This ensures we always use the proxy in development
  return ''  // Empty string = relative URLs = Vite proxy
}

const resolveWsUrl = (): string => {
  const envUrl = import.meta.env.VITE_WS_URL
  if (envUrl !== undefined && envUrl !== '') {
    return envUrl
  }
  return ''  // Empty string = relative URLs = Vite proxy
}

export const config: Config = {
  apiUrl: resolveApiUrl(),
  wsUrl: resolveWsUrl(),
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
