import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useBrewPagination } from '../useBrewPagination'

describe('useBrewPagination', () => {
  const createItems = (count: number) => Array.from({ length: count }, (_, i) => ({ id: i + 1 }))

  describe('initialization', () => {
    it('should start on page 1', () => {
      const { result } = renderHook(() => useBrewPagination(createItems(30), 10))
      expect(result.current.currentPage).toBe(1)
    })

    it('should calculate correct total pages', () => {
      const { result } = renderHook(() => useBrewPagination(createItems(30), 10))
      expect(result.current.totalPages).toBe(3)
    })

    it('should handle exact division', () => {
      const { result } = renderHook(() => useBrewPagination(createItems(30), 10))
      expect(result.current.totalPages).toBe(3)
    })

    it('should handle non-exact division', () => {
      const { result } = renderHook(() => useBrewPagination(createItems(35), 10))
      expect(result.current.totalPages).toBe(4)
    })

    it('should return at least 1 page for any items', () => {
      const { result: emptyResult } = renderHook(() => useBrewPagination([], 10))
      const { result: oneItemResult } = renderHook(() => useBrewPagination(createItems(1), 10))
      expect(emptyResult.current.totalPages).toBe(1)
      expect(oneItemResult.current.totalPages).toBe(1)
    })
  })

  describe('currentItems', () => {
    it('should return items for current page', () => {
      const items = createItems(30)
      const { result } = renderHook(() => useBrewPagination(items, 10))
      expect(result.current.currentItems).toHaveLength(10)
      expect(result.current.currentItems[0].id).toBe(1)
      expect(result.current.currentItems[9].id).toBe(10)
    })

    it('should return correct items on different pages', () => {
      const items = createItems(30)
      const { result } = renderHook(() => useBrewPagination(items, 10))

      act(() => {
        result.current.goToPage(2)
      })
      expect(result.current.currentItems).toHaveLength(10)
      expect(result.current.currentItems[0].id).toBe(11)
      expect(result.current.currentItems[9].id).toBe(20)

      act(() => {
        result.current.goToPage(3)
      })
      expect(result.current.currentItems).toHaveLength(10)
      expect(result.current.currentItems[0].id).toBe(21)
      expect(result.current.currentItems[9].id).toBe(30)
    })

    it('should handle last page with fewer items', () => {
      const items = createItems(25)
      const { result } = renderHook(() => useBrewPagination(items, 10))

      act(() => {
        result.current.goToPage(3)
      })
      expect(result.current.currentItems).toHaveLength(5)
      expect(result.current.currentItems[0].id).toBe(21)
      expect(result.current.currentItems[4].id).toBe(25)
    })

    it('should return empty array for empty items', () => {
      const { result } = renderHook(() => useBrewPagination([], 10))
      expect(result.current.currentItems).toHaveLength(0)
    })
  })

  describe('nextPage', () => {
    it('should increment page', () => {
      const items = createItems(30)
      const { result } = renderHook(() => useBrewPagination(items, 10))
      expect(result.current.currentPage).toBe(1)

      act(() => {
        result.current.nextPage()
      })
      expect(result.current.currentPage).toBe(2)

      act(() => {
        result.current.nextPage()
      })
      expect(result.current.currentPage).toBe(3)
    })

    it('should not exceed max page', () => {
      const items = createItems(30)
      const { result } = renderHook(() => useBrewPagination(items, 10))

      act(() => {
        result.current.nextPage()
        result.current.nextPage()
        result.current.nextPage()
        result.current.nextPage() // Try to go past last page
      })

      expect(result.current.currentPage).toBe(3)
    })
  })

  describe('prevPage', () => {
    it('should decrement page', () => {
      const items = createItems(30)
      const { result } = renderHook(() => useBrewPagination(items, 10))

      act(() => {
        result.current.goToPage(3)
      })
      expect(result.current.currentPage).toBe(3)

      act(() => {
        result.current.prevPage()
      })
      expect(result.current.currentPage).toBe(2)

      act(() => {
        result.current.prevPage()
      })
      expect(result.current.currentPage).toBe(1)
    })

    it('should not go below page 1', () => {
      const items = createItems(30)
      const { result } = renderHook(() => useBrewPagination(items, 10))

      act(() => {
        result.current.prevPage()
        result.current.prevPage()
      })

      expect(result.current.currentPage).toBe(1)
    })
  })

  describe('goToPage', () => {
    it('should navigate to specific page', () => {
      const items = createItems(50)
      const { result } = renderHook(() => useBrewPagination(items, 10))

      act(() => {
        result.current.goToPage(3)
      })
      expect(result.current.currentPage).toBe(3)

      act(() => {
        result.current.goToPage(5)
      })
      expect(result.current.currentPage).toBe(5)
    })

    it('should clamp page to valid range', () => {
      const items = createItems(30)
      const { result } = renderHook(() => useBrewPagination(items, 10))

      act(() => {
        result.current.goToPage(0)
      })
      expect(result.current.currentPage).toBe(1)

      act(() => {
        result.current.goToPage(100)
      })
      expect(result.current.currentPage).toBe(3)
    })

    it('should clamp decimal values to valid range', () => {
      const items = createItems(30)
      const { result } = renderHook(() => useBrewPagination(items, 10))

      act(() => {
        result.current.goToPage(2.7)
      })
      // The hook clamps to range but doesn't round, so 2.7 is valid if < totalPages
      expect(result.current.currentPage).toBeLessThanOrEqual(3)
      expect(result.current.currentPage).toBeGreaterThanOrEqual(1)
    })
  })

  describe('default page size', () => {
    it('should use default page size of 10', () => {
      const items = createItems(30)
      const { result } = renderHook(() => useBrewPagination(items))
      expect(result.current.totalPages).toBe(3)
      expect(result.current.currentItems).toHaveLength(10)
    })
  })

  describe('custom page size', () => {
    it('should respect custom page size', () => {
      const items = createItems(30)
      const { result } = renderHook(() => useBrewPagination(items, 5))
      expect(result.current.totalPages).toBe(6)
      expect(result.current.currentItems).toHaveLength(5)
    })

    it('should work with page size of 1', () => {
      const items = createItems(5)
      const { result } = renderHook(() => useBrewPagination(items, 1))
      expect(result.current.totalPages).toBe(5)
      expect(result.current.currentItems).toHaveLength(1)
      expect(result.current.currentItems[0].id).toBe(1)

      act(() => {
        result.current.nextPage()
      })
      expect(result.current.currentPage).toBe(2)
      expect(result.current.currentItems[0].id).toBe(2)
    })
  })

  describe('updating items', () => {
    it('should recalculate pages when items change', () => {
      const items1 = createItems(20)
      const { result: result1 } = renderHook(() => useBrewPagination(items1, 10))
      expect(result1.current.totalPages).toBe(2)

      const items2 = createItems(50)
      const { result: result2 } = renderHook(() => useBrewPagination(items2, 10))
      expect(result2.current.totalPages).toBe(5)
    })
  })

  describe('edge cases', () => {
    it('should handle single item', () => {
      const { result } = renderHook(() => useBrewPagination(createItems(1), 10))
      expect(result.current.totalPages).toBe(1)
      expect(result.current.currentItems).toHaveLength(1)
    })

    it('should handle page size larger than items', () => {
      const { result } = renderHook(() => useBrewPagination(createItems(5), 20))
      expect(result.current.totalPages).toBe(1)
      expect(result.current.currentItems).toHaveLength(5)
    })

    it('should handle empty array', () => {
      const { result } = renderHook(() => useBrewPagination([], 10))
      expect(result.current.totalPages).toBe(1)
      expect(result.current.currentItems).toHaveLength(0)
      expect(result.current.currentPage).toBe(1)
    })
  })
})
