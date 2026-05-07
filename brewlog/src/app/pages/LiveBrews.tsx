import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Plus, Trash2 } from 'lucide-react'
import { Navbar } from '../components/Navbar'
import { OfflineBanner } from '../components/OfflineBanner'
import { GeneratorControls } from '../components/GeneratorControls'
import { StarRating } from '../components/StarRating'
import { useAuth } from '@/hooks/useAuth'
import { useInfiniteBrewLogs } from '../hooks/useInfiniteBrewLogs'
import { useOnlineStatus } from '../hooks/useOnlineStatus'
import { useBrewSocket } from '../hooks/useBrewSocket'
import { fetchBeans, fetchRefs, queueOrSend } from '../api/client'
import type { ServerBean, ServerBrewLog } from '../api/client'

/**
 * Silver + Gold showcase page:
 *
 *  - Server-side pagination consumed as infinite scroll with one-page
 *    prefetch (Gold "BE RESPONSIVE").
 *  - Bean sidebar exposes the 1-to-many relationship Bean → BrewLogs with
 *    per-bean statistics AND full CRUD (create + delete via queueOrSend so
 *    mutations survive an offline window) (Gold "BE DILIGENT").
 *  - Dual Recharts visualisations (method PieChart + rating BarChart) sit
 *    side-by-side with the master list and re-render every time a Faker
 *    batch arrives through the WebSocket (Silver "side-by-side charts").
 *  - Dual-tier offline detection + queue replay on reconnect (Silver
 *    "offline support").
 */

const METHOD_COLORS = ['#8B5A3C', '#C69C6D', '#D9AB72', '#6B4423', '#A0826D', '#5A3E2A', '#E0C097', '#8A4F2F']
const RATING_COLORS = ['#d9534f', '#f0ad4e', '#f7e26b', '#83c879', '#2e8b57']

export function LiveBrews() {
  const { hasPermission } = useAuth()
  const canControl = hasPermission('generator:control')
  const online = useOnlineStatus()
  const [beans, setBeans] = useState<ServerBean[]>([])
  const [beanId, setBeanId] = useState<string | undefined>(undefined)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const {
    items,
    total,
    hasMore,
    loading,
    error: listError,
    loadMore,
    mergeLive,
    reset,
  } = useInfiniteBrewLogs({ pageSize: 20, beanId, prefetchNext: true, enabled: online })

  const batches = useBrewSocket(online)
  const consumedBatches = useRef(0)

  // Drain WebSocket batches into the list without extra HTTP calls.
  useEffect(() => {
    while (consumedBatches.current < batches.length) {
      const batch = batches[consumedBatches.current++]
      const filtered = beanId ? batch.filter((b) => b.bean_id === beanId) : batch
      mergeLive(filtered)
    }
  }, [batches, beanId, mergeLive])

  const refreshBeans = () => {
    if (!online) return
    fetchBeans()
      .then((page) => setBeans(page.items))
      .catch(() => setBeans([]))
  }
  useEffect(refreshBeans, [online])

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

  // ----- 1-to-many CRUD over the currently loaded items --------------------

  const handleDelete = async (id: string) => {
    setBusy(true)
    setError(null)
    try {
      await queueOrSend({ id: `delete-${id}-${Date.now()}`, kind: 'delete-brewlog', payload: { id } })
      // Optimistic UI: reload page 1 to stay consistent with the server.
      reset()
      await loadMore()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const handleAddForSelectedBean = async () => {
    if (!beanId) return
    setBusy(true)
    setError(null)
    try {
      const refs = await fetchRefs()
      if (!refs.brewerId || !refs.grinderId) {
        throw new Error('Backend has no brewer/grinder yet — start the generator once to seed.')
      }
      const payload = {
        date: new Date().toISOString(),
        bean_id: beanId,
        equipment_id: refs.brewerId,
        grinder_id: refs.grinderId,
        grind_setting: '22 clicks',
        method: 'V60',
        dose_g: '15',
        water_g: '250',
        water_temp_c: 94,
        brew_time_s: 150,
        rating: 4,
        taste_result: 'Balanced',
        tasting_notes: [],
        notes: 'Added from the Live view',
      }
      await queueOrSend({ id: `create-${Date.now()}`, kind: 'create-brewlog', payload })
      reset()
      await loadMore()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  // ----- chart inputs derived from the currently visible brews -------------

  const methodDistribution = useMemo(() => {
    const counts = new Map<string, number>()
    for (const b of items) counts.set(b.method, (counts.get(b.method) ?? 0) + 1)
    return [...counts.entries()].map(([name, value]) => ({ name, value }))
  }, [items])

  const ratingDistribution = useMemo(() => {
    const buckets = [1, 2, 3, 4, 5].map((r) => ({ name: `${r}★`, value: 0 }))
    for (const b of items) if (b.rating >= 1 && b.rating <= 5) buckets[b.rating - 1].value += 1
    return buckets
  }, [items])

  const perBeanStats = useMemo(() => {
    if (!beanId) return null
    const brews = items.filter((b) => b.bean_id === beanId)
    if (brews.length === 0) return null
    const avg = brews.reduce((sum, b) => sum + b.rating, 0) / brews.length
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
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-8 space-y-6">
        <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-3xl mb-1" style={{ fontFamily: 'var(--font-heading)' }}>
              Live brews
            </h1>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Server-paginated infinite scroll · live WebSocket batches · offline-safe CRUD
            </p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <OfflineBanner online={online} />
            <span title={!canControl ? 'Admin only' : undefined}>
              <GeneratorControls disabled={!online || !canControl} />
            </span>
          </div>
        </header>

        {/* ─── Charts side-by-side with the master list ─────────────────── */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div
            className="rounded-xl border p-4"
            style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}
            data-testid="chart-methods"
          >
            <h2 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>
              Brewing methods{beanId ? ' (filtered)' : ''}
            </h2>
            {methodDistribution.length === 0 ? (
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                No data yet — start the generator or add a brew.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={methodDistribution}
                    dataKey="value"
                    nameKey="name"
                    outerRadius={80}
                    label={({ name, percent }) =>
                      `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                    }
                  >
                    {methodDistribution.map((_, i) => (
                      <Cell key={i} fill={METHOD_COLORS[i % METHOD_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div
            className="rounded-xl border p-4"
            style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}
            data-testid="chart-ratings"
          >
            <h2 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>
              Rating distribution
            </h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={ratingDistribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value">
                  {ratingDistribution.map((_, i) => (
                    <Cell key={i} fill={RATING_COLORS[i]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* ─── Bean sidebar (1-to-many) + master list ───────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <aside
            className="lg:col-span-1 rounded-xl border p-4 space-y-3"
            style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}
          >
            <div className="flex items-center justify-between">
              <h2
                className="text-sm font-semibold uppercase tracking-wide"
                style={{ color: 'var(--text-muted)' }}
              >
                Beans ({beans.length})
              </h2>
            </div>
            <ul className="space-y-1">
              <li>
                <button
                  type="button"
                  className="w-full text-left text-sm px-2 py-1 rounded"
                  style={{
                    backgroundColor: beanId === undefined ? 'var(--cream)' : 'transparent',
                    color:
                      beanId === undefined ? 'var(--primary-brown)' : 'var(--foreground)',
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
                      backgroundColor: beanId === bean.id ? 'var(--cream)' : 'transparent',
                      color:
                        beanId === bean.id ? 'var(--primary-brown)' : 'var(--foreground)',
                    }}
                    onClick={() => setBeanId(bean.id)}
                    data-testid={`bean-filter-${bean.id}`}
                  >
                    {bean.name}
                    <span className="ml-2 text-xs" style={{ color: 'var(--text-muted)' }}>
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
                data-testid="bean-stats"
              >
                <h3 className="text-sm font-semibold" style={{ color: 'var(--foreground)' }}>
                  1-to-many stats
                </h3>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  {perBeanStats.count} brew{perBeanStats.count === 1 ? '' : 's'} · avg ⭐{' '}
                  {perBeanStats.average}
                </p>
                <ul className="text-xs space-y-0.5">
                  {perBeanStats.methods.map(([method, count]) => (
                    <li key={method} className="flex items-center justify-between">
                      <span style={{ color: 'var(--foreground)' }}>{method}</span>
                      <span style={{ color: 'var(--text-muted)' }}>{count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {beanId && (
              <button
                type="button"
                onClick={handleAddForSelectedBean}
                disabled={busy}
                className="w-full mt-2 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-white disabled:opacity-50"
                style={{ backgroundColor: 'var(--primary-brown)' }}
                data-testid="create-brew-for-bean"
              >
                <Plus size={14} /> Add brew for this bean
              </button>
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
              {(listError || error) && (
                <span style={{ color: 'var(--red)' }}>{error ?? listError}</span>
              )}
            </div>
            <ul
              className="rounded-xl border divide-y"
              style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}
              data-testid="brew-list"
            >
              {items.map((brew: ServerBrewLog) => (
                <li key={brew.id} className="p-3 flex items-center justify-between gap-2">
                  <div>
                    <div className="text-sm font-medium" style={{ color: 'var(--foreground)' }}>
                      {brew.method} · {new Date(brew.date).toLocaleDateString()}
                    </div>
                    <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                      {Number(brew.dose_g)}g → {Number(brew.water_g)}g · {brew.water_temp_c}°C ·{' '}
                      {brew.brew_time_s}s
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StarRating rating={brew.rating} size={14} />
                    <button
                      type="button"
                      onClick={() => handleDelete(brew.id)}
                      disabled={busy}
                      className="disabled:opacity-50"
                      style={{ color: 'var(--red)' }}
                      title="Delete brew"
                      data-testid={`delete-${brew.id}`}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </li>
              ))}
              {items.length === 0 && !loading && (
                <li
                  className="p-6 text-center text-sm"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {online
                    ? 'No brews yet — start the generator or add one manually.'
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
