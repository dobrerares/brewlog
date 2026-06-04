import { useCallback, useEffect, useState } from 'react'
import { Play, Square } from 'lucide-react'
import { generatorStatus, startGenerator, stopGenerator } from '../api/client'

interface Props {
  disabled?: boolean
}

/**
 * Silver-side control panel: toggles the server-side Faker loop that
 * produces batches of synthetic brewlogs and broadcasts them over the
 * WebSocket connection.
 */
export function GeneratorControls({ disabled }: Props) {
  const [running, setRunning] = useState(false)
  const [batches, setBatches] = useState(0)
  const [items, setItems] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const status = await generatorStatus()
      setRunning(status.running)
      setBatches(status.batches_emitted)
      setItems(status.items_emitted)
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    }
  }, [])

  useEffect(() => {
    if (disabled) return

    const firstRefresh = window.setTimeout(refresh, 0)
    const timer = window.setInterval(refresh, 3000)
    return () => {
      window.clearTimeout(firstRefresh)
      window.clearInterval(timer)
    }
  }, [disabled, refresh])

  const toggle = async () => {
    try {
      if (running) await stopGenerator()
      else await startGenerator(3, 2)
      await refresh()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div
      className="flex items-center gap-3 p-3 rounded-lg border"
      style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}
    >
      <button
        type="button"
        onClick={toggle}
        disabled={disabled}
        className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium text-white disabled:opacity-50 disabled:cursor-not-allowed"
        style={{ backgroundColor: running ? 'var(--red)' : 'var(--primary-brown)' }}
        data-testid="generator-toggle"
      >
        {running ? (
          <>
            <Square size={14} /> Stop generator
          </>
        ) : (
          <>
            <Play size={14} /> Start generator
          </>
        )}
      </button>
      <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
        <div>batches: {batches}</div>
        <div>items: {items}</div>
      </div>
      {error && (
        <div className="text-xs" style={{ color: 'var(--red)' }}>
          {error}
        </div>
      )}
    </div>
  )
}
