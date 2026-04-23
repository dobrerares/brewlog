import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import * as client from '../../api/client'
import type { Page, ServerBrewLog } from '../../api/client'
import { useInfiniteBrewLogs } from '../useInfiniteBrewLogs'

function brew(id: string, overrides: Partial<ServerBrewLog> = {}): ServerBrewLog {
  return {
    id,
    date: '2026-04-01T08:00:00',
    bean_id: 'bean-1',
    equipment_id: 'eq-1',
    grinder_id: 'gr-1',
    grind_setting: '22',
    method: 'V60',
    dose_g: 15,
    water_g: 250,
    water_temp_c: 94,
    brew_time_s: 150,
    yield_g: null,
    rating: 4,
    taste_result: 'Balanced',
    grind_adjustment: null,
    tasting_notes: [],
    notes: null,
    photo_url: null,
    ...overrides,
  }
}

function page(items: ServerBrewLog[], total: number, pageIndex: number, pageSize: number): Page<ServerBrewLog> {
  return {
    items,
    total,
    page: pageIndex,
    page_size: pageSize,
    total_pages: Math.ceil(total / pageSize),
  }
}

describe('useInfiniteBrewLogs', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('loads the first page automatically and prefetches the next', async () => {
    const spy = vi
      .spyOn(client, 'fetchBrewLogsPage')
      .mockImplementation(async (p) => {
        if (p === 1) return page([brew('a')], 4, 1, 2)
        if (p === 2) return page([brew('b')], 4, 2, 2)
        return page([], 4, p, 2)
      })

    const { result } = renderHook(() =>
      useInfiniteBrewLogs({ pageSize: 2 })
    )

    await waitFor(() => expect(result.current.items.length).toBe(1))
    // page 1 + prefetch of page 2
    await waitFor(() => expect(spy).toHaveBeenCalledTimes(2))
    expect(result.current.total).toBe(4)
    expect(result.current.totalPages).toBe(2)
    expect(result.current.hasMore).toBe(true)
  })

  it('serves the next loadMore from the prefetch cache', async () => {
    const spy = vi
      .spyOn(client, 'fetchBrewLogsPage')
      .mockImplementation(async (p) => {
        if (p === 1) return page([brew('a')], 3, 1, 1)
        if (p === 2) return page([brew('b')], 3, 2, 1)
        if (p === 3) return page([brew('c')], 3, 3, 1)
        return page([], 3, p, 1)
      })

    const { result } = renderHook(() =>
      useInfiniteBrewLogs({ pageSize: 1 })
    )
    await waitFor(() => expect(result.current.items.length).toBe(1))
    await waitFor(() => expect(spy).toHaveBeenCalledTimes(2))

    await act(async () => {
      await result.current.loadMore()
    })

    expect(result.current.items.map((b) => b.id)).toEqual(['a', 'b'])
  })

  it('surfaces fetch errors without swallowing them', async () => {
    vi.spyOn(client, 'fetchBrewLogsPage').mockRejectedValue(new Error('boom'))
    const { result } = renderHook(() => useInfiniteBrewLogs({ pageSize: 2 }))
    await waitFor(() => expect(result.current.error).toBe('boom'))
  })

  it('merges live items onto the first page and bumps the total', async () => {
    vi.spyOn(client, 'fetchBrewLogsPage').mockResolvedValue(
      page([brew('server-1')], 1, 1, 10)
    )
    const { result } = renderHook(() => useInfiniteBrewLogs({ pageSize: 10 }))
    await waitFor(() => expect(result.current.items.length).toBe(1))

    act(() => {
      result.current.mergeLive([brew('live-1'), brew('live-2')])
    })

    expect(result.current.items.map((b) => b.id)).toEqual([
      'live-1',
      'live-2',
      'server-1',
    ])
    expect(result.current.total).toBe(3)
  })

  it('dedupes merged items against what is already in page 1', async () => {
    vi.spyOn(client, 'fetchBrewLogsPage').mockResolvedValue(
      page([brew('shared')], 1, 1, 10)
    )
    const { result } = renderHook(() => useInfiniteBrewLogs({ pageSize: 10 }))
    await waitFor(() => expect(result.current.items.length).toBe(1))

    act(() => {
      result.current.mergeLive([brew('shared'), brew('new')])
    })
    const ids = result.current.items.map((b) => b.id)
    expect(ids.filter((id) => id === 'shared').length).toBe(1)
    expect(ids).toContain('new')
  })

  it('does nothing when disabled', async () => {
    const spy = vi.spyOn(client, 'fetchBrewLogsPage')
    renderHook(() => useInfiniteBrewLogs({ pageSize: 10, enabled: false }))
    await new Promise((r) => setTimeout(r, 10))
    expect(spy).not.toHaveBeenCalled()
  })
})
