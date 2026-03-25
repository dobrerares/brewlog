import { useState, useMemo } from 'react'

export function useBrewPagination<T>(items: T[], pageSize: number = 10) {
  const [currentPage, setCurrentPage] = useState(1)

  const totalPages = useMemo(() => {
    return Math.max(1, Math.ceil(items.length / pageSize))
  }, [items.length, pageSize])

  const currentItems = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize
    return items.slice(startIndex, startIndex + pageSize)
  }, [items, currentPage, pageSize])

  const nextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages))
  }

  const prevPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1))
  }

  const goToPage = (page: number) => {
    const validPage = Math.max(1, Math.min(page, totalPages))
    setCurrentPage(validPage)
  }

  return {
    currentPage,
    totalPages,
    currentItems,
    nextPage,
    prevPage,
    goToPage
  }
}
