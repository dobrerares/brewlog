import { useState, useCallback } from 'react'
import type { BrewLog } from '../data/mockData'
import { mockBrewLogs } from '../data/mockData'

// In-memory store that persists across hook instances
let brewsStore = [...mockBrewLogs]

export function useBrewCRUD() {
  const [brews, setBrews] = useState<BrewLog[]>(brewsStore)

  const createBrew = useCallback((brewData: Omit<BrewLog, 'id'>) => {
    const newBrew: BrewLog = {
      ...brewData,
      id: Date.now().toString()
    }
    brewsStore = [...brewsStore, newBrew]
    setBrews([...brewsStore])
    return newBrew
  }, [])

  const updateBrew = useCallback((id: string, updates: Partial<BrewLog>) => {
    const index = brewsStore.findIndex(b => b.id === id)
    if (index === -1) return false

    brewsStore[index] = { ...brewsStore[index], ...updates }
    setBrews([...brewsStore])
    return true
  }, [])

  const deleteBrew = useCallback((id: string) => {
    const initialLength = brewsStore.length
    brewsStore = brewsStore.filter(b => b.id !== id)
    setBrews([...brewsStore])
    return brewsStore.length < initialLength
  }, [])

  const getBrew = useCallback((id: string) => {
    return brews.find(b => b.id === id)
  }, [brews])

  const getBrews = useCallback(() => {
    return brews
  }, [brews])

  return {
    createBrew,
    updateBrew,
    deleteBrew,
    getBrew,
    getBrews
  }
}
