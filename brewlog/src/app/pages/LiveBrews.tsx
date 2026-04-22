import { useEffect, useMemo, useRef, useState } from 'react'
import { Navbar } from '../components/Navbar'
import { OfflineBanner } from '../components/OfflineBanner'
import { GeneratorControls } from '../components/GeneratorControls'
import { StarRating } from '../components/StarRating'
import { useInfiniteBrewLogs } from '../hooks/useInfiniteBrewLogs'
import { useOnlineStatus } from '../hooks/useOnlineStatus'
import { useBrewSocket } from '../hooks/useBrewSocket'
import { fetchBeans } from '../api/client'
import type { ServerBean } from '../api/client'

/**
 * Silver + Gold showcase page:
 *  - Consumes the backend's server-side pagination via infinite scroll with
 *    one-page prefetch (Gold "BE RESPONSIVE").
 *  - Sidebar drill-down by bean renders the 1-to-many relationship between
 *    beans and brew logs with per-bean statistics (Gold "BE DILIGENT").
 *  - Offline/online detection + queue replay (Silver "offline support").
 *  - WebSocket subscription merges live Faker batches at the top of the list
 *    (Silver "WebSocket alerts").
 */
export function LiveBrews() {
  const online = useOnlineStatus()
  const [beans, setBeans] = useState<ServerBean[]>([])
  const [beanId, setBeanId] = useState<string | undefined>(undefined)
  const { items, total, hasMore, loading, error, loadMore, mergeLive } =
    useInfiniteBrewLogs({ pageSize: 20, beanId, prefetchNext: true, enabled: online })

  const batches = useBrewSocket(online)
  const consumedBatches = useRef(0)

  // Drain WebSocket batches into the infinite list without a network round trip.
  useEffect(() => {
    while (consumedBatches.current < batches.length) {
      const batch = batches[consumedBatches.current++]
      const filtered = beanId ? batch.filter((b) => b.bean_id === beanId) : batch
      mergeLive(filtered)
    }
  }, [batches, beanId, mergeLive])

  useEffect(() => {
    if (!online) return
    fetchBeans()
      .then((page) => setBeans(page.items))
      .catch(() => setBeans([]))
  }, [online])

  // Infinite scroll trigger.
  const sentinel = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    const node = sentinel.current
    if (!node) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && hasMore && !loading) void loadMore()
      },
      { rootMargin: '320px 0px' }
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [hasMore, loading, loadMore])

  const perBeanStats = useMemo(() => {
    if (!beanId) return null
    const brews = items.filter((b) => b.bean_id === beanId)
    if (brews.length === 0) return null
    const avg =
      brews.reduce((sum, b) => sum + b.rating, 0) / brews.length
    const methods = new Map<string, number>()
    brews.forEach((b) => methods.set(b.method, (methods.get(b.method) ?? 0) + 1))
    return {
      count: brews.length,
      average: Number(avg.toFixed(2)),
      methods: [...methods.entries()].sort((a, b) => b[1] - a[1]),
    }
  }, [items, beanId])

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--background)' }}>
      <Navbar type="app" />
      <div className="max-w-6xl mx-auto px-4 sm:px-8 py-8 space-y-6">
        <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1
              className="text-3xl mb-1"
              style={{ fontFamily: 'var(--font-heading)' }}
            >
              Live brews
            </h1>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Server-paginated infinite scroll · live WebSocket batches
            </p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <OfflineBanner online={online} />
            <GeneratorControls disabled={!online} />
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <aside
            className="lg:col-span-1 rounded-xl border p-4 space-y-3"
            style={{
              backgroundColor: 'var(--card)',
              borderColor: 'var(--border-color)',
            }}
          >
            <h2
              className="text-sm font-semibold uppercase tracking-wide"
              style={{ color: 'var(--text-muted)' }}
            >
              Beans ({beans.length})
            </h2>
            <ul className="space-y-1">
              <li>
                <button
                  type="button"
                  className="w-full text-left text-sm px-2 py-1 rounded"
                  style={{
                    backgroundColor:
                      beanId === undefined ? 'var(--cream)' : 'transparent',
                    color:
                      beanId === undefined
                        ? 'var(--primary-brown)'
                        : 'var(--foreground)',
                  }}
                  onClick={() => setBeanId(undefined)}
                  data-testid="bean-filter-all"
                >
                  All beans
                </button>
              </li>
              {beans.map((bean) => (
                <li key={bean.id}>
                  <button
                    type="button"
                    className="w-full text-left text-sm px-2 py-1 rounded"
                    style={{
                      backgroundColor:
                        beanId === bean.id ? 'var(--cream)' : 'transparent',
                      color:
                        beanId === bean.id
                          ? 'var(--primary-brown)'
                          : 'var(--foreground)',
                    }}
                    onClick={() => setBeanId(bean.id)}
                    data-testid={`bean-filter-${bean.id}`}
                  >
                    {bean.name}
                    <span
                      className="ml-2 text-xs"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      {bean.origin_country}
                    </span>
                  </button>
                </li>
              ))}
            </ul>

            {perBeanStats && (
              <div
                className="mt-4 pt-4 border-t space-y-2 animate-fadeIn"
                style={{ borderColor: 'var(--border-color)' }}
              >
                <h3
                  className="text-sm font-semibold"
                  style={{ color: 'var(--foreground)' }}
                >
                  1-to-many stats
                </h3>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  {perBeanStats.count} brew{perBeanStats.count === 1 ? '' : 's'}
                  · avg ⭐ {perBeanStats.average}
                </p>
                <ul className="text-xs space-y-0.5">
                  {perBeanStats.methods.map(([method, count]) => (
                    <li
                      key={method}
                      className="flex items-center justify-between"
                    >
                      <span style={{ color: 'var(--foreground)' }}>{method}</span>
                      <span style={{ color: 'var(--text-muted)' }}>{count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </aside>

          <section className="lg:col-span-2 space-y-2">
            <div
              className="flex items-center justify-between text-xs"
              style={{ color: 'var(--text-muted)' }}
            >
              <span>
                Showing {items.length} of {total} brews
                {beanId ? ' for the selected bean' : ''}
              </span>
              {loading && <span>loading…</span>}
              {error && <span style={{ color: 'var(--red)' }}>{error}</span>}
            </div>
            <ul
              className="rounded-xl border divide-y"
              style={{
                backgroundColor: 'var(--card)',
                borderColor: 'var(--border-color)',
              }}
              data-testid="brew-list"
            >
              {items.map((brew) => (
                <li
                  key={brew.id}
                  className="p-3 flex items-center justify-between gap-2"
                >
                  <div>
                    <div
                      className="text-sm font-medium"
                      style={{ color: 'var(--foreground)' }}
                    >
                      {brew.method} ·{' '}
                      {new Date(brew.date).toLocaleDateString()}
                    </div>
                    <div
                      className="text-xs"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      {Number(brew.dose_g)}g → {Number(brew.water_g)}g ·
                      {brew.water_temp_c}°C · {brew.brew_time_s}s
                    </div>
                  </div>
                  <StarRating rating={brew.rating} size={14} />
                </li>
              ))}
              {items.length === 0 && !loading && (
                <li
                  className="p-6 text-center text-sm"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {online
                    ? 'No brews yet — start the generator or log one manually.'
                    : 'Offline. Reconnect to load brews from the server.'}
                </li>
              )}
            </ul>
            {hasMore && (
              <div
                ref={sentinel}
                style={{ color: 'var(--text-muted)' }}
                className="text-center text-xs py-4"
              >
                Scroll to load more…
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}
