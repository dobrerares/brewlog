import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useCookie } from '../useCookie'

beforeEach(() => {
  document.cookie.split(';').forEach(c => {
    document.cookie = c.trim().split('=')[0] + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/'
  })
})

describe('useCookie', () => {
  it('should return default value when cookie does not exist', () => {
    const { result } = renderHook(() => useCookie('test_cookie', 'default'))
    expect(result.current[0]).toBe('default')
  })

  it('should set and read a string cookie', () => {
    const { result } = renderHook(() => useCookie('test_cookie', ''))
    act(() => {
      result.current[1]('hello')
    })
    expect(result.current[0]).toBe('hello')
    expect(document.cookie).toContain('test_cookie=hello')
  })

  it('should set and read a JSON cookie', () => {
    const { result } = renderHook(() => useCookie('json_cookie', { count: 0 }))
    act(() => {
      result.current[1]({ count: 5 })
    })
    expect(result.current[0]).toEqual({ count: 5 })
  })

  it('should delete a cookie', () => {
    const { result } = renderHook(() => useCookie('del_cookie', 'val'))
    act(() => {
      result.current[1]('something')
    })
    act(() => {
      result.current[2]()
    })
    expect(result.current[0]).toBe('val')
  })

  it('should handle special characters in values', () => {
    const { result } = renderHook(() => useCookie('special', ''))
    act(() => {
      result.current[1]('hello world & more=stuff')
    })
    expect(result.current[0]).toBe('hello world & more=stuff')
  })
})
