import { useParams, Link, useNavigate } from 'react-router'
import { ArrowLeft, Trash2, Edit2 } from 'lucide-react'
import { useBrewCRUD } from '../hooks/useBrewCRUD'
import type { BrewLog } from '../data/mockData'

export function BrewDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { getBrew, deleteBrew } = useBrewCRUD()

  const brew = id ? getBrew(id) : null

  if (!brew) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--background)' }}>
        <div className="text-center">
          <p className="mb-4 text-base" style={{ color: 'var(--text-muted)' }}>
            Brew not found
          </p>
          <Link to="/brews" className="font-medium hover:opacity-60 transition-opacity" style={{ color: 'var(--primary-brown)' }}>
            Back to Brew Logs
          </Link>
        </div>
      </div>
    )
  }

  // Type guard for TypeScript
  const b = brew as BrewLog

  const handleDelete = () => {
    if (confirm('Delete this brew?')) {
      deleteBrew(id!)
      navigate('/brews')
    }
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--background)' }}>
      <nav style={{ borderColor: 'var(--border-color)' }} className="border-b">
        <div className="max-w-6xl mx-auto px-8 py-4 flex items-center justify-between">
          <Link to="/" style={{ color: 'var(--primary-brown)' }}>
            <h3 className="m-0">BrewLog</h3>
          </Link>
          <Link to="/brews" style={{ color: 'var(--foreground)' }} className="text-sm hover:opacity-60 transition-opacity">
            Brews
          </Link>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-8 py-12">
        <Link
          to="/brews"
          className="inline-flex items-center gap-2 mb-8 font-medium hover:opacity-60 transition-opacity"
          style={{ color: 'var(--primary-brown)' }}
        >
          <ArrowLeft size={16} /> Back to Brew Logs
        </Link>

        <div style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }} className="border rounded-lg p-8">
          <div className="flex items-start justify-between mb-8">
            <div>
              <h1 style={{ color: 'var(--primary-dark)' }} className="mb-2">
                {b.bean}
              </h1>
              <p style={{ color: 'var(--text-muted)' }} className="text-sm">
                {b.method} • {new Date(b.date).toLocaleDateString()}
              </p>
            </div>
            <div className="flex gap-2">
              <Link
                to={`/brew/${id}/edit`}
                className="flex items-center gap-2 px-4 py-2 rounded hover:opacity-90 transition-colors text-white text-sm font-medium"
                style={{ backgroundColor: 'var(--primary-brown)' }}
              >
                <Edit2 size={16} /> Edit
              </Link>
              <button
                onClick={handleDelete}
                className="flex items-center gap-2 px-4 py-2 rounded hover:opacity-90 transition-colors text-white text-sm font-medium"
                style={{ backgroundColor: 'var(--red)' }}
              >
                <Trash2 size={16} /> Delete
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-8 mb-8">
            <div>
              <h3 className="font-semibold mb-4" style={{ color: 'var(--primary-brown)' }}>Brewing Parameters</h3>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt style={{ color: 'var(--text-muted)' }}>Dose:</dt>
                  <dd className="font-medium" style={{ color: 'var(--foreground)' }}>{b.dose}g</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: 'var(--text-muted)' }}>Water:</dt>
                  <dd className="font-medium" style={{ color: 'var(--foreground)' }}>{b.water}g</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: 'var(--text-muted)' }}>Temperature:</dt>
                  <dd className="font-medium" style={{ color: 'var(--foreground)' }}>{b.temp}°C</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: 'var(--text-muted)' }}>Brew Time:</dt>
                  <dd className="font-medium" style={{ color: 'var(--foreground)' }}>{b.time}</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: 'var(--text-muted)' }}>Grind:</dt>
                  <dd className="font-medium" style={{ color: 'var(--foreground)' }}>{b.grind}</dd>
                </div>
              </dl>
            </div>

            <div>
              <h3 className="font-semibold mb-4" style={{ color: 'var(--primary-brown)' }}>Review</h3>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt style={{ color: 'var(--text-muted)' }}>Rating:</dt>
                  <dd className="font-medium" style={{ color: 'var(--foreground)' }}>{'⭐'.repeat(b.rating)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: 'var(--text-muted)' }}>Taste:</dt>
                  <dd className="font-medium" style={{ color: 'var(--foreground)' }}>{b.taste}</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: 'var(--text-muted)' }}>Grinder:</dt>
                  <dd className="font-medium" style={{ color: 'var(--foreground)' }}>{b.grinder}</dd>
                </div>
                {b.brewer && (
                  <div className="flex justify-between">
                    <dt style={{ color: 'var(--text-muted)' }}>Brewer:</dt>
                    <dd className="font-medium" style={{ color: 'var(--foreground)' }}>{b.brewer}</dd>
                  </div>
                )}
              </dl>
            </div>
          </div>

          <div>
            <h3 className="font-semibold mb-2" style={{ color: 'var(--primary-brown)' }}>Notes</h3>
            <p className="whitespace-pre-wrap" style={{ color: 'var(--text-muted)' }}>{b.notes || '(No notes)'}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
