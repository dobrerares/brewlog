import { useCallback, useEffect } from 'react'
import { useCookie } from './useCookie'

type Theme = 'light' | 'dark'

export function useTheme() {
  const [theme, setTheme] = useCookie<Theme>('brewlog_theme', 'light')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const toggleTheme = useCallback(() => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }, [theme, setTheme])

  return { theme, toggleTheme }
}
