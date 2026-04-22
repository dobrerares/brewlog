import { useEffect, useRef, useState } from 'react'
import { API_BASE } from '../api/client'
import type { ServerBrewLog } from '../api/client'

/**
 * Subscribe to the backend's WebSocket endpoint and surface brewlog batches as
 * React state. Reconnects with exponential backoff up to 30 s.
 *
 * Emits the entire batch at once so consumers can merge the items into their
 * local state in a single render.
 */
export function useBrewSocket(enabled = true): ServerBrewLog[][] {
  const [batches, setBatches] = useState<ServerBrewLog[][]>([])
  const retryRef = useRef(1000)
  const closedRef = useRef(false)

  useEffect(() => {
    if (!enabled) return
    closedRef.current = false
    let socket: WebSocket | null = null
    let retryTimer: number | null = null

    const connect = () => {
      try {
        socket = new WebSocket(`${API_BASE.replace(/^http/, 'ws')}/ws`)
      } catch {
        scheduleReconnect()
        return
      }
      socket.addEventListener('open', () => {
        retryRef.current = 1000
      })
      socket.addEventListener('message', (event) => {
        try {
          const payload = JSON.parse(event.data) as { type: string; items?: ServerBrewLog[] }
          if (payload.type === 'brewlog.batch' && Array.isArray(payload.items)) {
            setBatches((prev) => [...prev, payload.items ?? []])
          }
        } catch {
          // ignore malformed frames
        }
      })
      socket.addEventListener('close', () => {
        if (!closedRef.current) scheduleReconnect()
      })
      socket.addEventListener('error', () => {
        socket?.close()
      })
    }

    const scheduleReconnect = () => {
      retryTimer = window.setTimeout(connect, retryRef.current)
      retryRef.current = Math.min(retryRef.current * 2, 30_000)
    }

    connect()

    return () => {
      closedRef.current = true
      if (retryTimer !== null) window.clearTimeout(retryTimer)
      socket?.close()
    }
  }, [enabled])

  return batches
}
