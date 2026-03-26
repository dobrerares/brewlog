import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router'
import { ArrowLeft } from 'lucide-react'
import { Navbar } from '../components/Navbar'
import { StarRating } from '../components/StarRating'
import { TasteBadge } from '../components/TasteBadge'
import { FlavorTag } from '../components/FlavorTag'
import { DeleteConfirmModal } from '../components/DeleteConfirmModal'
import { useBrewCRUD } from '../hooks/useBrewCRUD'
import { useActivityTracker } from '../hooks/useActivityTracker'
import type { BrewLog } from '../data/mockData'

export function BrewDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { getBrew, deleteBrew } = useBrewCRUD()
  const [showDeleteModal, setShowDeleteModal] = useState(false)

  const brew = id ? getBrew(id) : null

  if (!brew) {
    return (
      <div className="min-h-screen" style={{ backgroundColor: 'var(--background)' }}>
        <Navbar type="app" />
        <div className="max-w-3xl mx-auto px-8 py-8 text-center">
          <p className="mb-4 text-base" style={{ color: 'var(--text-muted)' }}>Brew not found</p>
          <Link to="/brews" className="font-medium hover:opacity-60 transition-opacity" style={{ color: 'var(--primary-brown)' }}>
            Back to Brew Logs
          </Link>
        </div>
      </div>
    )
  }

  const b = brew as BrewLog
  const { setLastViewed, trackVisit } = useActivityTracker()
  useEffect(() => {
    trackVisit(`/brew/${id}`)
    setLastViewed({ id: id!, bean: b.bean })
  }, [id])

  const handleDelete = () => {
    deleteBrew(id!)
    setShowDeleteModal(false)
    navigate('/brews')
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--background)' }}>
      <Navbar type="app" />

      <div className="max-w-3xl mx-auto px-4 sm:px-8 py-8">
        <Link
          to="/brews"
          className="inline-flex items-center gap-1 text-sm hover:underline mb-6"
          style={{ color: 'var(--primary-brown)' }}
        >
          <ArrowLeft size={16} /> Back to brew logs
        </Link>

        <div className="rounded-xl border p-6 sm:p-8 animate-fadeIn" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
          {/* Header */}
          <div className="flex flex-col sm:flex-row items-start justify-between mb-6 gap-4">
            <div>
              <h1 className="text-3xl mb-2" style={{ fontFamily: 'var(--font-heading)' }}>
                {b.bean}
              </h1>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                {b.method} · {new Date(b.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Link
                to={`/brew/${id}/edit`}
                className="px-4 py-2 rounded-lg border transition-colors text-sm font-medium"
                style={{ backgroundColor: 'var(--cream)', color: 'var(--primary-brown)', borderColor: 'var(--border-color)' }}
              >
                Edit
              </Link>
              <button
                onClick={() => setShowDeleteModal(true)}
                className="px-4 py-2 rounded-lg border transition-colors text-sm font-medium"
                style={{ backgroundColor: '#B85C4A15', color: 'var(--red)', borderColor: '#B85C4A30' }}
              >
                Delete
              </button>
            </div>
          </div>

          {/* Rating & Taste */}
          <div className="flex items-center gap-3 mb-8">
            <StarRating rating={b.rating} size={20} />
            <TasteBadge taste={b.taste} />
          </div>

          {/* Parameters Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
            {[
              { label: 'Dose', value: `${b.dose}g` },
              { label: 'Water', value: `${b.water}g` },
              { label: 'Temp', value: `${b.temp}°C` },
              { label: 'Time', value: b.time },
              { label: 'Grind', value: b.grind },
              { label: 'Grinder', value: b.grinder },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-lg p-4" style={{ backgroundColor: 'var(--cream)' }}>
                <p className="text-xs mb-1 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>{label}</p>
                <p className="text-xl font-semibold" style={{ color: 'var(--primary-dark)' }}>{value}</p>
              </div>
            ))}
          </div>

          {b.brewer && (
            <div className="rounded-lg p-4 mb-8" style={{ backgroundColor: 'var(--cream)' }}>
              <p className="text-xs mb-1 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Brewer</p>
              <p className="text-lg font-semibold" style={{ color: 'var(--primary-dark)' }}>{b.brewer}</p>
            </div>
          )}

          {/* Flavor Tags */}
          {b.flavorTags.length > 0 && (
            <div className="mb-8">
              <p className="text-xs font-semibold mb-3 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>
                Tasting notes
              </p>
              <div className="flex flex-wrap gap-2">
                {b.flavorTags.map(tag => (
                  <FlavorTag key={tag} label={tag} selected />
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          <div>
            <p className="text-xs font-semibold mb-3 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>
              Notes
            </p>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--foreground)' }}>
              {b.notes || '(No notes)'}
            </p>
          </div>
        </div>
      </div>

      <DeleteConfirmModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDelete}
      />
    </div>
  )
}
