import { useCallback, useMemo } from 'react'
import { useCookie } from './useCookie'

interface LastViewed {
  id: string
  bean: string
}

type VisitMap = Record<string, number>

export function useActivityTracker() {
  const [visits, setVisits] = useCookie<VisitMap>('brewlog_visits', {})
  const [lastViewed, setLastViewedCookie] = useCookie<LastViewed | null>('brewlog_last_viewed', null)

  const trackVisit = useCallback((path: string) => {
    setVisits((currentVisits) => ({
      ...currentVisits,
      [path]: (currentVisits[path] || 0) + 1,
    }))
  }, [setVisits])

  const setLastViewed = useCallback((brew: LastViewed) => {
    setLastViewedCookie(brew)
  }, [setLastViewedCookie])

  const totalVisits = useMemo(() => {
    return Object.values(visits).reduce((sum, count) => sum + count, 0)
  }, [visits])

  const brewsLogged = visits['/brew/new'] || 0

  return {
    visits,
    trackVisit,
    lastViewed,
    setLastViewed,
    totalVisits,
    brewsLogged,
  }
}
