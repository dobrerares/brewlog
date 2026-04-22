import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useOnlineStatus } from '../useOnlineStatus'

describe('useOnlineStatus', () => {
  beforeEach(() => {
    Object.defineProperty(navigator, 'onLine', {
      configurable: true,
      get: () => true,
    })
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'ok' }), { status: 200 }))
    )
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('reports online when the server health probe succeeds', async () => {
    const { result } = renderHook(() => useOnlineStatus(5_000))
    await waitFor(() => expect(result.current).toBe(true))
  })

  it('flips to offline when the server probe fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('refused')))
    const { result } = renderHook(() => useOnlineStatus(5_000))
    await waitFor(() => expect(result.current).toBe(false))
  })

  it('reacts to the window offline event', async () => {
    const { result } = renderHook(() => useOnlineStatus(5_000))
    await waitFor(() => expect(result.current).toBe(true))
    act(() => {
      Object.defineProperty(navigator, 'onLine', {
        configurable: true,
        get: () => false,
      })
      window.dispatchEvent(new Event('offline'))
    })
    expect(result.current).toBe(false)
  })
})
