import { useEffect, useState, useRef, useCallback } from 'react'

interface UseWebSocketOptions {
  onMessage?: (data: unknown) => void
  onConnect?: () => void
  onDisconnect?: () => void
  enabled?: boolean
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { enabled = true } = options
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<unknown>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)
  const optionsRef = useRef(options)
  const mountedRef = useRef(false)
  
  // Keep options ref updated
  useEffect(() => {
    optionsRef.current = options
  }, [options])

  const connect = useCallback(() => {
    // Skip if disabled or already connecting/connected
    if (!enabled) return
    if (!mountedRef.current) return
    if (wsRef.current?.readyState === WebSocket.CONNECTING || 
        wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }
    
    try {
      // Connect directly to backend to avoid VPN/proxy issues
      const wsUrl = 'ws://127.0.0.1:8000/api/v1/ws'
      
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        if (!mountedRef.current) {
          ws.close()
          return
        }
        setConnected(true)
        optionsRef.current.onConnect?.()
        // Subscribe to all channels
        ws.send(JSON.stringify({ type: 'subscribe', channels: ['attacks', 'alerts', 'honeypots'] }))
      }

      ws.onmessage = (event) => {
        if (!mountedRef.current) return
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
          optionsRef.current.onMessage?.(data)
        } catch {
          // Ignore parse errors
        }
      }

      ws.onclose = () => {
        if (!mountedRef.current) return
        setConnected(false)
        optionsRef.current.onDisconnect?.()
        wsRef.current = null
        // Reconnect after 5 seconds
        reconnectTimeout.current = setTimeout(connect, 5000)
      }

      ws.onerror = () => {
        // Error will trigger onclose, which handles reconnect
        // Don't log - reduces console noise
      }

      wsRef.current = ws
    } catch {
      // Failed to create WebSocket - retry later
      if (mountedRef.current) {
        reconnectTimeout.current = setTimeout(connect, 5000)
      }
    }
  }, [enabled])

  useEffect(() => {
    mountedRef.current = true
    
    if (enabled) {
      // Delay initial connection slightly
      const initTimeout = setTimeout(connect, 100)
      
      return () => {
        clearTimeout(initTimeout)
        mountedRef.current = false
        if (reconnectTimeout.current) {
          clearTimeout(reconnectTimeout.current)
        }
        if (wsRef.current) {
          wsRef.current.close()
          wsRef.current = null
        }
      }
    }
    
    return () => {
      mountedRef.current = false
    }
  }, [connect, enabled])

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  return { connected, lastMessage, send }
}