import { useEffect, useState } from 'react'
import { Cloud, CloudOff, RefreshCw } from 'lucide-react'
import { queueSize } from '../api/offlineQueue'
import { syncQueue } from '../api/client'

interface Props {
  online: boolean
  onSynced?: () => void
}

/**
 * Sticky banner that reflects offline state and lets the user force a sync
 * once the connection returns. Auto-drains the queue on reconnect.
 */
export function OfflineBanner({ online, onSynced }: Props) {
  const [pending, setPending] = useState(queueSize())
  const [syncing, setSyncing] = useState(false)

  useEffect(() => {
    setPending(queueSize())
  }, [online])

  useEffect(() => {
    if (!online || pending === 0) return
    let cancelled = false
    setSyncing(true)
    syncQueue()
      .then(() => {
        if (cancelled) return
        setPending(queueSize())
        onSynced?.()
      })
      .finally(() => {
        if (!cancelled) setSyncing(false)
      })
    return () => {
      cancelled = true
    }
  }, [online, pending, onSynced])

  if (online && pending === 0) {
    return (
      <div
        className="flex items-center gap-2 px-3 py-1 rounded-full text-xs"
        style={{ backgroundColor: 'var(--cream)', color: 'var(--primary-brown)' }}
        data-testid="connection-indicator"
      >
        <Cloud size={14} /> Online
      </div>
    )
  }

  if (!online) {
    return (
      <div
        className="flex items-center gap-2 px-3 py-1 rounded-full text-xs animate-fadeIn"
        style={{ backgroundColor: '#ffe2c7', color: '#a14a00' }}
        data-testid="connection-indicator"
      >
        <CloudOff size={14} />
        Offline — {pending} pending
      </div>
    )
  }

  return (
    <div
      className="flex items-center gap-2 px-3 py-1 rounded-full text-xs animate-fadeIn"
      style={{ backgroundColor: '#d9f1e1', color: '#0f6a33' }}
      data-testid="connection-indicator"
    >
      <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
      Syncing — {pending} pending
    </div>
  )
}
