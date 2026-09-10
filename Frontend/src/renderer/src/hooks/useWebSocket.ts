import { useEffect, useRef, useState } from 'react'
import {
  createWebSocketConnection,
  type WebSocketConnection,
  type WsConnectionStatus
} from '../services/websocket.service'
import type { ClientEvent, ServerEvent } from '../types/api'

interface UseWebSocketReturn {
  status: WsConnectionStatus
  send: (event: ClientEvent) => void
  lastEvent: ServerEvent | null
  disconnect: () => void
  reconnect: () => void
}

/**
 * Session-scoped WebSocket hook. Automatically connects when mounted and
 * disconnects when sessionId changes or the component unmounts.
 */
export function useWebSocket(sessionId: string | null): UseWebSocketReturn {
  const [status, setStatus] = useState<WsConnectionStatus>('closed')
  const [lastEvent, setLastEvent] = useState<ServerEvent | null>(null)
  const connRef = useRef<WebSocketConnection | null>(null)

  function connect() {
    if (!sessionId) return
    if (connRef.current) {
      connRef.current.disconnect()
    }
    
    const conn = createWebSocketConnection(
      sessionId,
      (event) => setLastEvent(event),
      (s) => setStatus(s)
    )
    connRef.current = conn
  }

  useEffect(() => {
    connect()
    return () => {
      connRef.current?.disconnect()
      connRef.current = null
    }
  }, [sessionId])

  return {
    status,
    lastEvent,
    send: (event) => connRef.current?.send(event),
    disconnect: () => connRef.current?.disconnect(),
    reconnect: connect
  }
}
