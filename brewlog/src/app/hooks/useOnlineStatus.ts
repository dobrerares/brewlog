import { useEffect, useRef, useState } from 'react'
import { API_BASE } from '../api/client'

/**
 * Two-tier online status.
 *
 * 1. `navigator.onLine` catches OS-level loss (e.g. wifi off).
 * 2. A periodic /health probe catches "online but server unreachable" — the
 *    Silver challenge asks us to detect both.
 *
 * Consumers receive a single boolean; they don't need to distinguish the two
 * failure modes.
 */
export function useOnlineStatus(pollMs = 10_000): boolean {
  const [online, setOnline] = useState(
    typeof navigator === 'undefined' ? true : navigator.onLine
  )
  const timer = useRef<number | null>(null)

  useEffect(() => {
    if (typeof window === 'undefined') return
    const handleOnline = () => setOnline(true)
    const handleOffline = () => setOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    const probe = async () => {
      if (!navigator.onLine) {
        setOnline(false)
        return
      }
      try {
        const response = await fetch(`${API_BASE}/health`, { cache: 'no-store' })
        setOnline(response.ok)
      } catch {
        setOnline(false)
      }
    }

    void probe()
    timer.current = window.setInterval(probe, pollMs)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      if (timer.current !== null) window.clearInterval(timer.current)
    }
  }, [pollMs])

  return online
}
