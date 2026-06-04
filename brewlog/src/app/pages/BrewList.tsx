import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { ChevronRight, Plus, Trash2 } from 'lucide-react'
import { Navbar } from '../components/Navbar'
import { StarRating } from '../components/StarRating'
import { TasteBadge } from '../components/TasteBadge'
import { DeleteConfirmModal } from '../components/DeleteConfirmModal'
import { useBrewCRUD } from '../hooks/useBrewCRUD'
import { useBrewPagination } from '../hooks/useBrewPagination'
import { useActivityTracker } from '../hooks/useActivityTracker'

export function BrewList() {
  const { getBrews, deleteBrew } = useBrewCRUD()
  const { currentItems, currentPage, totalPages, nextPage, prevPage } = useBrewPagination(getBrews(), 10)
  const { trackVisit } = useActivityTracker()
  useEffect(() => { trackVisit('/brews') }, [trackVisit])

  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)

  const handleDelete = () => {
    if (deleteTarget) {
      deleteBrew(deleteTarget)
      setDeleteTarget(null)
    }
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--background)' }}>
      <Navbar type="app" />

      <div className="max-w-5xl mx-auto px-4 sm:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl mb-1" style={{ fontFamily: 'var(--font-heading)' }}>
              Brew Logs
            </h1>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{getBrews().length} brews logged</p>
          </div>
          <Link
            to="/brew/new"
            className="flex items-center gap-2 px-6 py-3 text-white rounded-lg hover:opacity-90 transition-colors font-medium"
            style={{ backgroundColor: 'var(--primary-brown)' }}
          >
            <Plus size={20} /> New brew
          </Link>
        </div>

        {currentItems.length === 0 ? (
          <div className="text-center py-20 rounded-xl border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
            <p className="mb-6 text-base" style={{ color: 'var(--text-muted)' }}>
              No brew logs yet. Start logging!
            </p>
            <Link
              to="/brew/new"
              className="inline-block px-6 py-3 rounded-lg hover:opacity-90 transition-colors font-medium text-white"
              style={{ backgroundColor: 'var(--primary-brown)' }}
            >
              Log Your First Brew
            </Link>
          </div>
        ) : (
          <div className="rounded-xl border overflow-hidden" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
            {/* Desktop table */}
            <div className="hidden sm:block overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--background)' }}>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Date</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Bean</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Method</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Rating</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Taste</th>
                    <th className="w-20"></th>
                  </tr>
                </thead>
                <tbody>
                  {currentItems.map((brew) => (
                    <tr
                      key={brew.id}
                      className="border-b last:border-0 transition-colors hover:opacity-80"
                      style={{ borderColor: 'var(--border-color)' }}
                    >
                      <td className="px-6 py-4 text-sm" style={{ color: 'var(--text-muted)' }}>
                        {new Date(brew.date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
                      </td>
                      <td className="px-6 py-4 text-sm font-medium" style={{ color: 'var(--foreground)' }}>{brew.bean}</td>
                      <td className="px-6 py-4 text-sm" style={{ color: 'var(--text-muted)' }}>{brew.method}</td>
                      <td className="px-6 py-4"><StarRating rating={brew.rating} /></td>
                      <td className="px-6 py-4"><TasteBadge taste={brew.taste} /></td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2 items-center justify-end">
                          <Link to={`/brew/${brew.id}`} style={{ color: 'var(--text-muted)' }} className="hover:opacity-70">
                            <ChevronRight size={20} />
                          </Link>
                          <button
                            onClick={() => setDeleteTarget(brew.id)}
                            className="hover:opacity-70 transition-colors"
                            style={{ color: 'var(--red)' }}
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="sm:hidden divide-y" style={{ borderColor: 'var(--border-color)' }}>
              {currentItems.map((brew) => (
                <div key={brew.id} className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium" style={{ color: 'var(--foreground)' }}>{brew.bean}</span>
                    <StarRating rating={brew.rating} size={14} />
                  </div>
                  <div className="flex items-center justify-between text-xs" style={{ color: 'var(--text-muted)' }}>
                    <span>{brew.method} · {new Date(brew.date).toLocaleDateString()}</span>
                    <TasteBadge taste={brew.taste} />
                  </div>
                  <div className="flex gap-3 pt-1">
                    <Link to={`/brew/${brew.id}`} className="text-xs font-medium" style={{ color: 'var(--primary-brown)' }}>View →</Link>
                    <button onClick={() => setDeleteTarget(brew.id)} className="text-xs" style={{ color: 'var(--red)' }}>Delete</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {totalPages > 1 && (
          <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Page {currentPage} of {totalPages}
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={prevPage}
                disabled={currentPage === 1}
                className="px-4 py-2 text-sm border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)', color: 'var(--foreground)' }}
              >
                ← Prev
              </button>
              <button
                onClick={nextPage}
                disabled={currentPage === totalPages}
                className="px-4 py-2 text-sm border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)', color: 'var(--foreground)' }}
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </div>

      <DeleteConfirmModal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
      />
    </div>
  )
}
