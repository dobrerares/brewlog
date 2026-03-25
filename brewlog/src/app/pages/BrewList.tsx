import { Link } from 'react-router'
import { Plus, Trash2 } from 'lucide-react'
import { useBrewCRUD } from '../hooks/useBrewCRUD'
import { useBrewPagination } from '../hooks/useBrewPagination'

export function BrewList() {
  const { getBrews, deleteBrew } = useBrewCRUD()
  const { currentItems, currentPage, totalPages, nextPage, prevPage } = useBrewPagination(getBrews(), 10)

  const handleDelete = (id: string) => {
    if (confirm('Delete this brew log?')) {
      deleteBrew(id)
    }
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--background)' }}>
      <nav style={{ borderColor: 'var(--border-color)' }} className="border-b">
        <div className="max-w-6xl mx-auto px-8 py-4 flex items-center justify-between">
          <Link to="/" style={{ color: 'var(--primary-brown)' }}>
            <h3 className="m-0">BrewLog</h3>
          </Link>
          <Link to="/" style={{ color: 'var(--foreground)' }} className="text-sm hover:opacity-60 transition-opacity">
            Home
          </Link>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-8 py-12">
        <div className="flex items-center justify-between mb-12">
          <h1 style={{ color: 'var(--primary-dark)' }} className="m-0">
            Brew Logs
          </h1>
          <Link
            to="/brew/new"
            className="flex items-center gap-2 px-6 py-3 rounded-lg hover:opacity-90 transition-colors text-base font-medium"
            style={{
              backgroundColor: 'var(--primary-brown)',
              color: '#FFFFFF'
            }}
          >
            <Plus size={20} /> New Brew
          </Link>
        </div>

        {currentItems.length === 0 ? (
          <div className="text-center py-20 rounded-lg border" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
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
          <div style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }} className="border rounded-lg overflow-hidden">
            <table className="w-full">
              <thead>
                <tr style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--background)' }} className="border-b">
                  <th className="px-6 py-4 text-left text-sm font-medium" style={{ color: 'var(--primary-brown)' }}>
                    Date
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium" style={{ color: 'var(--primary-brown)' }}>
                    Bean
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium" style={{ color: 'var(--primary-brown)' }}>
                    Method
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium" style={{ color: 'var(--primary-brown)' }}>
                    Rating
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium" style={{ color: 'var(--primary-brown)' }}>
                    Taste
                  </th>
                  <th className="px-6 py-4 text-center text-sm font-medium" style={{ color: 'var(--primary-brown)' }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {currentItems.map((brew) => (
                  <tr
                    key={brew.id}
                    style={{ borderColor: 'var(--border-color)' }}
                    className="border-b hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-6 py-4 text-sm" style={{ color: 'var(--foreground)' }}>
                      {new Date(brew.date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium" style={{ color: 'var(--foreground)' }}>
                      {brew.bean}
                    </td>
                    <td className="px-6 py-4 text-sm" style={{ color: 'var(--text-muted)' }}>
                      {brew.method}
                    </td>
                    <td className="px-6 py-4 text-sm" style={{ color: 'var(--foreground)' }}>
                      {'⭐'.repeat(brew.rating)}
                    </td>
                    <td className="px-6 py-4 text-sm" style={{ color: 'var(--text-muted)' }}>
                      {brew.taste}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex gap-2 justify-center">
                        <Link
                          to={`/brew/${brew.id}`}
                          className="text-sm font-medium hover:opacity-80 transition-colors"
                          style={{ color: 'var(--primary-brown)' }}
                        >
                          View
                        </Link>
                        <button
                          onClick={() => handleDelete(brew.id)}
                          className="hover:opacity-80 transition-colors"
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
        )}

        {totalPages > 1 && (
          <div className="mt-8 flex items-center justify-center gap-4">
            <button
              onClick={prevPage}
              disabled={currentPage === 1}
              className="px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium text-white"
              style={{ backgroundColor: 'var(--primary-brown)' }}
            >
              Previous
            </button>
            <span className="text-sm font-medium" style={{ color: 'var(--primary-brown)' }}>
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={nextPage}
              disabled={currentPage === totalPages}
              className="px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium text-white"
              style={{ backgroundColor: 'var(--primary-brown)' }}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
