/**
 * localStorage-backed queue of mutations that failed (or were skipped) because
 * the client was offline. Replayed in insertion order on reconnect.
 */

const KEY = 'brewlog_offline_queue'

export type QueuedMutation =
  | { id: string; kind: 'create-brewlog'; payload: Record<string, unknown> }
  | {
      id: string
      kind: 'patch-brewlog'
      payload: { id: string; patch: Record<string, unknown> }
    }
  | { id: string; kind: 'delete-brewlog'; payload: { id: string } }

function read(): QueuedMutation[] {
  if (typeof localStorage === 'undefined') return []
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as QueuedMutation[]) : []
  } catch {
    return []
  }
}

function write(queue: QueuedMutation[]): void {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(KEY, JSON.stringify(queue))
}

export function queueSize(): number {
  return read().length
}

export function enqueue(mutation: QueuedMutation): void {
  const queue = read()
  queue.push(mutation)
  write(queue)
}

export function peek(): QueuedMutation[] {
  return read()
}

export function clearQueue(): void {
  write([])
}

/**
 * Replay queued mutations sequentially. Successfully applied entries are
 * removed from the queue; the first failure halts the drain and leaves the
 * remainder queued for a future attempt.
 */
export async function drainQueue(
  handler: (mutation: QueuedMutation) => Promise<void>
): Promise<void> {
  const queue = read()
  while (queue.length > 0) {
    const next = queue[0]
    try {
      await handler(next)
    } catch {
      return
    }
    queue.shift()
    write(queue)
  }
}
