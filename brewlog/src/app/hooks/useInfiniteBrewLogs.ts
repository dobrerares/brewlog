import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { fetchBrewLogsPage } from '../api/client'
import type { ServerBrewLog } from '../api/client'

interface Options {
  pageSize?: number
  beanId?: string
  prefetchNext?: boolean
  enabled?: boolean
}

/**
 * Gold "BE RESPONSIVE": infinite scroll fueled by the backend's server-side
 * pagination. The next page is prefetched as soon as the current one lands,
 * so scrolling only blocks the UI when the user outpaces the prefetch
 * (which, at pageSize=20, happens well before the network is the bottleneck).
 *
 * Additionally supports live merges — consumers can push WebSocket batches
 * into the hook via `mergeLive`, which prepends items to page 1 without
 * re-issuing any HTTP requests.
 */
export function useInfiniteBrewLogs(options: Options = {}) {
  const { pageSize = 20, beanId, prefetchNext = true, enabled = true } = options

  const [pages, setPages] = useState<ServerBrewLog[][]>([])
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const prefetched = useRef<Map<number, ServerBrewLog[]>>(new Map())
  const inFlight = useRef<Set<number>>(new Set())

  const reset = useCallback(() => {
    setPages([])
    setTotal(0)
    setTotalPages(0)
    setError(null)
    prefetched.current.clear()
    inFlight.current.clear()
  }, [])

  const fetchPage = useCallback(
    async (
      page: number
    ): Promise<{ items: ServerBrewLog[]; totalPages: number } | null> => {
      if (inFlight.current.has(page)) return null
      inFlight.current.add(page)
      try {
        const response = await fetchBrewLogsPage(page, pageSize, { beanId })
        setTotal(response.total)
        setTotalPages(response.total_pages)
        return { items: response.items, totalPages: response.total_pages }
      } finally {
        inFlight.current.delete(page)
      }
    },
    [pageSize, beanId]
  )

  const loadMore = useCallback(async () => {
    if (!enabled) return
    setLoading(true)
    setError(null)
    try {
      const nextPageIndex = pages.length + 1
      const cached = prefetched.current.get(nextPageIndex)
      let items: ServerBrewLog[] | null = null
      let knownTotalPages = totalPages
      if (cached) {
        items = cached
        prefetched.current.delete(nextPageIndex)
      } else {
        const fetched = await fetchPage(nextPageIndex)
        if (fetched) {
          items = fetched.items
          knownTotalPages = fetched.totalPages
        }
      }
      if (items) setPages((prev) => [...prev, items!])

      if (prefetchNext) {
        const lookAhead = nextPageIndex + 1
        if (
          lookAhead <= knownTotalPages &&
          !prefetched.current.has(lookAhead)
        ) {
          fetchPage(lookAhead)
            .then((res) => {
              if (res) prefetched.current.set(lookAhead, res.items)
            })
            .catch(() => {
              /* soft-fail the prefetch; user will retry when scrolling */
            })
        }
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [enabled, pages.length, fetchPage, prefetchNext, totalPages])

  // Initial load + reload whenever the filter changes.
  useEffect(() => {
    if (!enabled) return
    reset()
    void loadMore()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, beanId, pageSize])

  const items = useMemo(() => pages.flat(), [pages])
  const hasMore = totalPages === 0 ? false : pages.length < totalPages

  const mergeLive = useCallback((newItems: ServerBrewLog[]) => {
    if (newItems.length === 0) return
    setPages((prev) => {
      if (prev.length === 0) return [[...newItems]]
      const [first, ...rest] = prev
      const seen = new Set(first.map((b) => b.id))
      const deduped = [...newItems.filter((b) => !seen.has(b.id)), ...first]
      return [deduped, ...rest]
    })
    setTotal((prev) => prev + newItems.length)
  }, [])

  return {
    items,
    total,
    totalPages,
    loading,
    error,
    hasMore,
    loadMore,
    reset,
    mergeLive,
  }
}
