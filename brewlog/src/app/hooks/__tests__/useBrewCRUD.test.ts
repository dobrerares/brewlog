import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useBrewCRUD } from '../useBrewCRUD'
import type { BrewLog } from '../../data/mockData'

const createTestBrew = (overrides = {}) => ({
  bean: 'Test Bean',
  method: 'V60',
  date: '2024-01-01',
  dose: 18,
  water: 300,
  temp: 90,
  time: '3:00',
  grind: '22',
  grinder: 'Baratza',
  rating: 4,
  taste: 'Balanced' as const,
  flavorTags: [],
  notes: 'Test brew',
  ...overrides
})

describe('useBrewCRUD', () => {
  describe('createBrew', () => {
    it('should create a new brew with auto-generated ID', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let created: BrewLog | undefined
      act(() => {
        created = result.current.createBrew(createTestBrew({ bean: 'Ethiopia Yirgacheffe' }))
      })
      expect(created!.id).toBeDefined()
      expect(created!.id).not.toEqual('')
      expect(created!.bean).toBe('Ethiopia Yirgacheffe')
    })

    it('should add brew to the store', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let initialCount: number = 0
      act(() => {
        initialCount = result.current.getBrews().length
      })

      act(() => {
        result.current.createBrew(createTestBrew())
      })

      let updated: BrewLog[] = []
      act(() => {
        updated = result.current.getBrews()
      })
      expect(updated).toHaveLength(initialCount + 1)
    })

    it('should create brews with IDs', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let brew1: BrewLog | undefined
      let brew2: BrewLog | undefined

      act(() => {
        brew1 = result.current.createBrew(createTestBrew({ bean: 'Bean1' }))
        // Different objects should have IDs
      })

      act(() => {
        brew2 = result.current.createBrew(createTestBrew({ bean: 'Bean2', date: '2024-01-02' }))
      })

      // Both should have valid IDs
      expect(brew1!.id).toBeDefined()
      expect(brew2!.id).toBeDefined()
    })
  })

  describe('getBrew', () => {
    it('should retrieve brew by ID', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let created: BrewLog | undefined
      act(() => {
        created = result.current.createBrew(createTestBrew({ bean: 'Test Bean' }))
      })

      let retrieved: BrewLog | undefined
      act(() => {
        retrieved = result.current.getBrew(created!.id)
      })
      expect(retrieved).toBeDefined()
      expect(retrieved?.bean).toBe('Test Bean')
      expect(retrieved?.id).toBe(created!.id)
    })

    it('should return undefined for non-existent ID', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let retrieved
      act(() => {
        retrieved = result.current.getBrew('non-existent-id')
      })
      expect(retrieved).toBeUndefined()
    })
  })

  describe('getBrews', () => {
    it('should return all brews', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let brews
      act(() => {
        brews = result.current.getBrews()
      })
      expect(Array.isArray(brews)).toBe(true)
      expect(brews!.length).toBeGreaterThan(0)
    })

    it('should include newly created brews', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let initialCount
      act(() => {
        initialCount = result.current.getBrews().length
      })

      act(() => {
        result.current.createBrew(createTestBrew())
      })

      expect(result.current.getBrews().length).toBe(initialCount! + 1)
    })
  })

  describe('updateBrew', () => {
    it('should update brew properties', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let created: BrewLog | undefined
      act(() => {
        created = result.current.createBrew(createTestBrew({ bean: 'Original', rating: 3, taste: 'Sour' }))
      })

      let success: boolean = false
      act(() => {
        success = result.current.updateBrew(created!.id, {
          bean: 'Updated',
          rating: 5,
          taste: 'Balanced'
        })
      })

      expect(success).toBe(true)
      let updated: BrewLog | undefined
      act(() => {
        updated = result.current.getBrew(created!.id)
      })
      expect(updated?.bean).toBe('Updated')
      expect(updated?.rating).toBe(5)
      expect(updated?.taste).toBe('Balanced')
      // Unchanged properties should remain
      expect(updated?.method).toBe('V60')
    })

    it('should return false for non-existent ID', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let success
      act(() => {
        success = result.current.updateBrew('non-existent-id', { rating: 5 })
      })
      expect(success).toBe(false)
    })

    it('should handle partial updates', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let created: BrewLog | undefined
      act(() => {
        created = result.current.createBrew(createTestBrew({ rating: 3, notes: 'Original notes' }))
      })

      act(() => {
        result.current.updateBrew(created!.id, { rating: 4 })
      })

      let updated: BrewLog | undefined
      act(() => {
        updated = result.current.getBrew(created!.id)
      })
      expect(updated?.rating).toBe(4)
      expect(updated?.notes).toBe('Original notes')
    })
  })

  describe('deleteBrew', () => {
    it('should remove brew from store', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let created
      act(() => {
        created = result.current.createBrew(createTestBrew({ bean: 'To Delete' }))
      })

      let initialCount
      act(() => {
        initialCount = result.current.getBrews().length
      })

      let success
      act(() => {
        success = result.current.deleteBrew(created!.id)
      })

      expect(success).toBe(true)
      expect(result.current.getBrews().length).toBe(initialCount! - 1)
    })

    it('should return false for non-existent ID', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let success
      act(() => {
        success = result.current.deleteBrew('non-existent-id')
      })
      expect(success).toBe(false)
    })

    it('should successfully delete a brew', () => {
      const { result } = renderHook(() => useBrewCRUD())
      let brewed: BrewLog | undefined

      act(() => {
        brewed = result.current.createBrew(createTestBrew({ bean: 'Test to Delete' }))
      })

      // Verify brew exists
      let existsBefore: BrewLog | undefined
      act(() => {
        existsBefore = result.current.getBrew(brewed!.id)
      })
      expect(existsBefore).toBeDefined()

      // Delete the brew
      let deleteSuccess = false
      act(() => {
        deleteSuccess = result.current.deleteBrew(brewed!.id)
      })

      expect(deleteSuccess).toBe(true)

      // Verify brew no longer exists
      let existsAfter: BrewLog | undefined
      act(() => {
        existsAfter = result.current.getBrew(brewed!.id)
      })
      expect(existsAfter).toBeUndefined()
    })
  })

  describe('data persistence across hook instances', () => {
    it('should persist data across multiple hook instances', () => {
      const { result: hook1Result } = renderHook(() => useBrewCRUD())
      act(() => {
        hook1Result.current.createBrew(createTestBrew({ bean: 'Shared Brew' }))
      })

      const { result: hook2Result } = renderHook(() => useBrewCRUD())
      let brews: BrewLog[] | undefined
      act(() => {
        brews = hook2Result.current.getBrews()
      })
      const found = brews!.some((b: BrewLog) => b.bean === 'Shared Brew')
      expect(found).toBe(true)
    })
  })
})
