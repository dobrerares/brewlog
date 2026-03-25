import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useActivityTracker } from '../useActivityTracker'

beforeEach(() => {
  document.cookie.split(';').forEach(c => {
    document.cookie = c.trim().split('=')[0] + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/'
  })
})

describe('useActivityTracker', () => {
  it('should start with zero visits', () => {
    const { result } = renderHook(() => useActivityTracker())
    expect(result.current.visits).toEqual({})
  })

  it('should track a page visit', () => {
    const { result } = renderHook(() => useActivityTracker())
    act(() => {
      result.current.trackVisit('/brews')
    })
    expect(result.current.visits['/brews']).toBe(1)
  })

  it('should increment existing visits', () => {
    const { result } = renderHook(() => useActivityTracker())
    act(() => {
      result.current.trackVisit('/brews')
    })
    act(() => {
      result.current.trackVisit('/brews')
    })
    expect(result.current.visits['/brews']).toBe(2)
  })

  it('should set and get last viewed brew', () => {
    const { result } = renderHook(() => useActivityTracker())
    act(() => {
      result.current.setLastViewed({ id: '123', bean: 'Test Bean' })
    })
    expect(result.current.lastViewed).toEqual({ id: '123', bean: 'Test Bean' })
  })

  it('should return null when no last viewed', () => {
    const { result } = renderHook(() => useActivityTracker())
    expect(result.current.lastViewed).toBeNull()
  })

  it('should calculate total visits', () => {
    const { result } = renderHook(() => useActivityTracker())
    act(() => {
      result.current.trackVisit('/brews')
    })
    act(() => {
      result.current.trackVisit('/brews')
    })
    act(() => {
      result.current.trackVisit('/brew/new')
    })
    expect(result.current.totalVisits).toBe(3)
  })
})
