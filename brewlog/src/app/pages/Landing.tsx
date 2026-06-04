import { useEffect } from 'react'
import { Link } from 'react-router'
import { Coffee, Clock, Target, BarChart3 } from 'lucide-react'
import { Navbar } from '../components/Navbar'
import { useActivityTracker } from '../hooks/useActivityTracker'
import { useBrewCRUD } from '../hooks/useBrewCRUD'

export function Landing() {
  const { lastViewed, totalVisits, brewsLogged, trackVisit } = useActivityTracker()
  const { getBrew } = useBrewCRUD()
  const lastBrew = lastViewed ? getBrew(lastViewed.id) : null

  useEffect(() => { trackVisit('/') }, [trackVisit])

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--background)' }}>
      <Navbar type="landing" />

      <div className="max-w-4xl mx-auto px-8 py-24 text-center animate-fadeIn">
        <Coffee size={48} style={{ color: 'var(--accent-terracotta)' }} className="mx-auto mb-6" strokeWidth={2} />

        <h1 className="text-5xl mb-4" style={{ fontFamily: 'var(--font-heading)', color: 'var(--primary-dark)' }}>
          BrewLog
        </h1>

        <p className="text-xl font-medium mb-6" style={{ color: 'var(--accent-terracotta)' }}>
          Your coffee journal.
        </p>

        <div className="w-24 h-px mx-auto mb-8" style={{ backgroundColor: 'var(--border-color)' }} />

        <p className="text-base max-w-lg mx-auto mb-12 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
          Track every brew with precision. Log beans, equipment, and roasters — dial in your grind with extraction
          feedback and build a searchable history of your coffee journey. All in one place.
        </p>

        {(totalVisits > 0 || lastBrew) && (
          <div className="mb-12 p-6 rounded-lg border text-sm animate-fadeIn" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
            {totalVisits > 0 && (
              <p style={{ color: 'var(--text-muted)' }}>
                Welcome back! You've visited {totalVisits} times{brewsLogged > 0 ? ` and logged ${brewsLogged} brews` : ''}.
              </p>
            )}
            {lastBrew && (
              <p className="mt-2">
                <Link to={`/brew/${lastBrew.id}`} className="font-medium hover:opacity-70 transition-opacity" style={{ color: 'var(--primary-brown)' }}>
                  Continue where you left off → {lastBrew.bean}
                </Link>
              </p>
            )}
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          <Link
            to="/register"
            className="px-8 py-3 rounded-lg hover:opacity-90 transition-colors text-base font-medium text-white"
            style={{ backgroundColor: 'var(--primary-brown)' }}
          >
            Get started
          </Link>
          <Link
            to="/login"
            className="px-8 py-3 rounded-lg hover:opacity-90 transition-colors text-base font-medium border"
            style={{
              backgroundColor: 'var(--cream)',
              color: 'var(--primary-brown)',
              borderColor: 'var(--border-color)'
            }}
          >
            Log in
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-3xl mx-auto">
          <div className="flex flex-col items-center">
            <Clock size={32} style={{ color: 'var(--accent-terracotta)' }} className="mb-3" />
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Guided brew timer</p>
          </div>
          <div className="flex flex-col items-center">
            <Target size={32} style={{ color: 'var(--accent-terracotta)' }} className="mb-3" />
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Grind dial-in</p>
          </div>
          <div className="flex flex-col items-center">
            <BarChart3 size={32} style={{ color: 'var(--accent-terracotta)' }} className="mb-3" />
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Brew statistics</p>
          </div>
        </div>
      </div>
    </div>
  )
}
