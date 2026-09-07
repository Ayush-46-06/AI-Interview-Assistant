// Session-scoped WebSocket service.
// Usage:
//   const conn = createWebSocketConnection(sessionId, onEvent)
//   conn.send({ event: 'start_recording' })
//   conn.disconnect()
//
// There is NO global singleton — each interview session gets its own instance.
// This prevents cross-session data leakage.

import { buildWsUrl } from './api'
import type { ClientEvent, ServerEvent } from '../types/api'

export type WsEventHandler = (event: ServerEvent) => void
export type WsStatusHandler = (status: WsConnectionStatus) => void

export type WsConnectionStatus = 'connecting' | 'open' | 'closed' | 'error'

export interface WebSocketConnection {
  send: (event: ClientEvent) => void
  disconnect: () => void
  getStatus: () => WsConnectionStatus
}

export function createWebSocketConnection(
  sessionId: string,
  onEvent: WsEventHandler,
  onStatusChange?: WsStatusHandler
): WebSocketConnection {
  let ws: WebSocket | null = null
  let status: WsConnectionStatus = 'connecting'
  let destroyed = false

  function setStatus(s: WsConnectionStatus): void {
    status = s
    onStatusChange?.(s)
  }

  function connect(): void {
    if (destroyed) return
    const url = buildWsUrl(sessionId)
    ws = new WebSocket(url)
    setStatus('connecting')

    ws.onopen = () => {
      setStatus('open')
    }

    ws.onmessage = (msgEvent) => {
      try {
        const parsed = JSON.parse(msgEvent.data as string) as ServerEvent
        onEvent(parsed)
      } catch {
        // malformed message — ignore
      }
    }

    ws.onerror = () => {
      setStatus('error')
    }

    ws.onclose = () => {
      if (!destroyed) {
        setStatus('closed')
      }
    }
  }

  connect()

  return {
    send(event: ClientEvent): void {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(event))
      }
    },

    disconnect(): void {
      destroyed = true
      if (ws) {
        ws.onclose = null // prevent status update after intentional close
        ws.close(1000, 'Session ended')
        ws = null
      }
      setStatus('closed')
    },

    getStatus(): WsConnectionStatus {
      return status
    }
  }
}
