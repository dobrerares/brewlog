import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  clearQueue,
  drainQueue,
  enqueue,
  peek,
  queueSize,
} from '../offlineQueue'
import type { QueuedMutation } from '../offlineQueue'

const make = (id: string): QueuedMutation => ({
  id,
  kind: 'create-brewlog',
  payload: { note: id },
})

describe('offlineQueue', () => {
  beforeEach(() => {
    clearQueue()
  })
  afterEach(() => {
    clearQueue()
    vi.restoreAllMocks()
  })

  it('starts empty', () => {
    expect(queueSize()).toBe(0)
    expect(peek()).toEqual([])
  })

  it('persists enqueued mutations', () => {
    enqueue(make('a'))
    enqueue(make('b'))
    expect(queueSize()).toBe(2)
    expect(peek().map((m) => m.id)).toEqual(['a', 'b'])
  })

  it('drains in FIFO order when handler succeeds', async () => {
    enqueue(make('a'))
    enqueue(make('b'))
    const seen: string[] = []
    await drainQueue(async (m) => {
      seen.push(m.id)
    })
    expect(seen).toEqual(['a', 'b'])
    expect(queueSize()).toBe(0)
  })

  it('halts the drain on first failure and keeps the rest queued', async () => {
    enqueue(make('a'))
    enqueue(make('b'))
    enqueue(make('c'))
    const seen: string[] = []
    await drainQueue(async (m) => {
      seen.push(m.id)
      if (m.id === 'b') throw new Error('boom')
    })
    expect(seen).toEqual(['a', 'b'])
    expect(peek().map((m) => m.id)).toEqual(['b', 'c'])
  })

  it('tolerates a corrupted localStorage payload', () => {
    localStorage.setItem('brewlog_offline_queue', '{not-json')
    expect(queueSize()).toBe(0)
  })
})
