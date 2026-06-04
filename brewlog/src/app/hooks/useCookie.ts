import { useState, useCallback, type SetStateAction } from 'react'

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
  return match ? decodeURIComponent(match[2]) : null
}

function setCookieRaw(name: string, value: string, maxAge = 2592000) {
  document.cookie = `${name}=${encodeURIComponent(value)};path=/;SameSite=Lax;max-age=${maxAge}`
}

function deleteCookieRaw(name: string) {
  document.cookie = `${name}=;path=/;expires=Thu, 01 Jan 1970 00:00:00 GMT`
}

export function useCookie<T>(name: string, defaultValue: T): [T, (value: SetStateAction<T>) => void, () => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    const raw = getCookie(name)
    if (raw === null) return defaultValue
    try {
      return typeof defaultValue === 'string' ? raw as unknown as T : JSON.parse(raw)
    } catch {
      return raw as unknown as T
    }
  })

  const setValue = useCallback((value: SetStateAction<T>) => {
    setStoredValue((previous) => {
      const nextValue = typeof value === 'function' ? (value as (current: T) => T)(previous) : value
      const toStore = typeof nextValue === 'string' ? nextValue : JSON.stringify(nextValue)
      setCookieRaw(name, toStore)
      return nextValue
    })
  }, [name])

  const removeCookie = useCallback(() => {
    deleteCookieRaw(name)
    setStoredValue(defaultValue)
  }, [name, defaultValue])

  return [storedValue, setValue, removeCookie]
}
