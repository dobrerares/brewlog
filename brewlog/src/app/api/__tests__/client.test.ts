import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  fetchBeans,
  fetchBrewLogsPage,
  fetchRefs,
  type ServerBean,
  type ServerBrewLog,
} from '../client'

const jsonResponse = (body: unknown) =>
  new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })

const brew = (id: string): ServerBrewLog => ({
  id,
  date: '2026-04-01T08:00:00',
  bean_id: 'bean-1',
  equipment_id: 'eq-1',
  grinder_id: 'gr-1',
  grind_setting: '22',
  method: 'V60',
  dose_g: 15,
  water_g: 250,
  water_temp_c: 94,
  brew_time_s: 150,
  yield_g: null,
  rating: 4,
  taste_result: 'Balanced',
  grind_adjustment: null,
  tasting_notes: [],
  notes: null,
  photo_url: null,
})

const bean = (id: string): ServerBean => ({
  id,
  name: `Bean ${id}`,
  roaster_id: null,
  origin_country: 'Romania',
  roast_level: 'Medium',
  process: 'Washed',
  tasting_notes: [],
})

describe('API client pagination normalization', () => {
  const mockFetch = vi.fn()

  beforeEach(() => {
    mockFetch.mockReset()
    vi.stubGlobal('fetch', mockFetch)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('keeps paginated REST responses as pages', async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({
        items: [brew('server-1')],
        total: 3,
        page: 1,
        page_size: 2,
        total_pages: 2,
      })
    )

    const page = await fetchBrewLogsPage(1, 2)

    expect(page.items.map((item) => item.id)).toEqual(['server-1'])
    expect(page.total).toBe(3)
    expect(page.total_pages).toBe(2)
  })

  it('normalizes raw list REST responses into client-side pages', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([brew('a'), brew('b'), brew('c')]))

    const page = await fetchBrewLogsPage(2, 2)

    expect(page.items.map((item) => item.id)).toEqual(['c'])
    expect(page.total).toBe(3)
    expect(page.page).toBe(2)
    expect(page.page_size).toBe(2)
    expect(page.total_pages).toBe(2)
  })

  it('normalizes raw bean lists', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([bean('a'), bean('b')]))

    const page = await fetchBeans(1, 1)

    expect(page.items.map((item) => item.id)).toEqual(['a'])
    expect(page.total).toBe(2)
    expect(page.total_pages).toBe(2)
  })

  it('builds quick-create refs from raw list endpoints', async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse([bean('bean-1')]))
      .mockResolvedValueOnce(
        jsonResponse([
          { id: 'grinder-1', type: 'Grinder' },
          { id: 'brewer-1', type: 'Brewer' },
        ])
      )

    await expect(fetchRefs()).resolves.toEqual({
      beanId: 'bean-1',
      brewerId: 'brewer-1',
      grinderId: 'grinder-1',
    })
  })
})
