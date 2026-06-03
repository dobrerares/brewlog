/**
 * Backend API client — REST + GraphQL.
 *
 * Silver challenge: every mutation is routed through `queueOrSend`, which
 * either hits the network when online or enqueues the request in
 * `offlineQueue` so it can be replayed once the connection returns.
 *
 * Gold challenge: `fetchBrewLogsPage` and `fetchBeanBrewLogs` are the
 * pagination + 1-to-many entry points the UI consumes.
 */

import { drainQueue, enqueue } from './offlineQueue'
import type { QueuedMutation } from './offlineQueue'

export const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export class NetworkError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'NetworkError'
  }
}

export interface ServerBrewLog {
  id: string
  date: string
  bean_id: string
  equipment_id: string
  grinder_id: string
  grind_setting: string
  method: string
  dose_g: string | number
  water_g: string | number
  water_temp_c: number
  brew_time_s: number
  yield_g: string | number | null
  rating: number
  taste_result: string | null
  grind_adjustment: string | null
  tasting_notes: string[]
  notes: string | null
  photo_url: string | null
}

export interface ServerBean {
  id: string
  name: string
  roaster_id: string | null
  origin_country: string
  roast_level: string
  process: string
  tasting_notes: string[]
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

async function request<T>(path: string, init?: RequestInit, retry = true): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
      credentials: 'include',
      ...init,
    })
  } catch (err) {
    throw new NetworkError((err as Error).message)
  }
  const canRefresh = path !== '/api/v1/auth/refresh' && path !== '/api/v1/auth/login/verify-mfa'
  if (response.status === 401 && retry && canRefresh) {
    const refreshed = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    })
    if (refreshed.ok) return request<T>(path, init, false)
    window.dispatchEvent(new CustomEvent('brewlog:session-expired'))
  }
  if (!response.ok) {
    const body = await response.text()
    throw new Error(`HTTP ${response.status}: ${body}`)
  }
  if (response.status === 204) return undefined as unknown as T
  return (await response.json()) as T
}

export async function fetchBrewLogsPage(
  page: number,
  pageSize: number,
  filters: { beanId?: string; method?: string } = {}
): Promise<Page<ServerBrewLog>> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (filters.beanId) params.set('bean_id', filters.beanId)
  if (filters.method) params.set('method', filters.method)
  return request<Page<ServerBrewLog>>(`/api/v1/brewlogs?${params}`)
}

export async function fetchBeans(page = 1, pageSize = 50): Promise<Page<ServerBean>> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  return request<Page<ServerBean>>(`/api/v1/beans?${params}`)
}

/**
 * Gold 1-to-many via GraphQL: fetch a bean together with every brewlog that
 * references it, plus the bean-scoped statistics the UI displays side by side.
 */
export async function fetchBeanWithBrewLogs(beanId: string): Promise<{
  bean: ServerBean
  brewlogs: ServerBrewLog[]
}> {
  const query = `
    query ($id: UUID!) {
      bean(id: $id) {
        id name roasterId originCountry roastLevel process tastingNotes
        brewlogs {
          id date method rating tasteResult doseG waterG waterTempC brewTimeS notes
        }
      }
    }
  `
  const resp = await request<{
    data: { bean: Record<string, unknown> | null }
    errors?: { message: string }[]
  }>('/graphql', { method: 'POST', body: JSON.stringify({ query, variables: { id: beanId } }) })
  if (resp.errors?.length) throw new Error(resp.errors[0].message)
  if (!resp.data.bean) throw new Error('bean not found')
  const b = resp.data.bean as Record<string, unknown>
  const brewlogs = (b.brewlogs as Array<Record<string, unknown>>).map((x) => ({
    id: x.id as string,
    date: x.date as string,
    bean_id: beanId,
    equipment_id: '',
    grinder_id: '',
    grind_setting: '',
    method: x.method as string,
    dose_g: x.doseG as number,
    water_g: x.waterG as number,
    water_temp_c: x.waterTempC as number,
    brew_time_s: x.brewTimeS as number,
    yield_g: null,
    rating: x.rating as number,
    taste_result: (x.tasteResult as string) ?? null,
    grind_adjustment: null,
    tasting_notes: [],
    notes: (x.notes as string) ?? null,
    photo_url: null,
  })) as ServerBrewLog[]
  return {
    bean: {
      id: b.id as string,
      name: b.name as string,
      roaster_id: (b.roasterId as string) ?? null,
      origin_country: b.originCountry as string,
      roast_level: b.roastLevel as string,
      process: b.process as string,
      tasting_notes: b.tastingNotes as string[],
    },
    brewlogs,
  }
}

export async function startGenerator(batchSize: number, intervalS: number): Promise<void> {
  await request('/api/v1/generator/start', {
    method: 'POST',
    body: JSON.stringify({ batch_size: batchSize, interval_s: intervalS }),
  })
}

export async function stopGenerator(): Promise<void> {
  await request('/api/v1/generator/stop', { method: 'POST' })
}

export async function generatorStatus(): Promise<{
  running: boolean
  batches_emitted: number
  items_emitted: number
}> {
  return request('/api/v1/generator/status')
}

/**
 * Fetch a valid reference set (any bean + any brewer + any grinder) so the UI
 * can populate a quick-create form without asking the user to pick every FK.
 * Used by the 1-to-many Live view's "Add brew" action.
 */
export async function fetchRefs(): Promise<{
  beanId: string | null
  brewerId: string | null
  grinderId: string | null
}> {
  const [beans, equipment] = await Promise.all([
    request<{ items: Array<{ id: string }> }>('/api/v1/beans?page_size=1'),
    request<{ items: Array<{ id: string; type: string }> }>(
      '/api/v1/equipment?page_size=50'
    ),
  ])
  const brewer = equipment.items.find((e) => e.type === 'Brewer') ?? null
  const grinder = equipment.items.find((e) => e.type === 'Grinder') ?? null
  return {
    beanId: beans.items[0]?.id ?? null,
    brewerId: brewer?.id ?? null,
    grinderId: grinder?.id ?? null,
  }
}

/**
 * Dispatch a mutation. When offline, the call is transparently queued for
 * replay the next time the network returns.
 */
export async function queueOrSend(mutation: QueuedMutation): Promise<void> {
  if (!navigator.onLine) {
    enqueue(mutation)
    return
  }
  try {
    await executeMutation(mutation)
  } catch (err) {
    if (err instanceof NetworkError) {
      enqueue(mutation)
      return
    }
    throw err
  }
}

export async function executeMutation(mutation: QueuedMutation): Promise<void> {
  switch (mutation.kind) {
    case 'create-brewlog':
      await request('/api/v1/brewlogs', {
        method: 'POST',
        body: JSON.stringify(mutation.payload),
      })
      return
    case 'delete-brewlog':
      await request(`/api/v1/brewlogs/${mutation.payload.id}`, { method: 'DELETE' })
      return
    case 'patch-brewlog':
      await request(`/api/v1/brewlogs/${mutation.payload.id}`, {
        method: 'PATCH',
        body: JSON.stringify(mutation.payload.patch),
      })
      return
  }
}

/** Replay every queued mutation. Returns the number of successful replays. */
export async function syncQueue(): Promise<number> {
  let replayed = 0
  await drainQueue(async (mutation) => {
    await executeMutation(mutation)
    replayed += 1
  })
  return replayed
}
