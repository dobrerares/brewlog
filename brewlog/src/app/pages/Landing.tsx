import { Link } from 'react-router'
import { Coffee, Clock, Target, BarChart3 } from 'lucide-react'

export function Landing() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)' }}>
      {/* Navigation */}
      <nav style={{ borderColor: 'var(--border-color)' }} className="border-b">
        <div className="max-w-4xl mx-auto px-8 py-4 flex items-center justify-between">
          <h3 style={{ color: 'var(--primary-brown)' }} className="m-0">
            BrewLog
          </h3>
          <div className="flex gap-8 text-sm">
            <Link to="/brews" style={{ color: 'var(--foreground)' }} className="hover:opacity-60 transition-opacity">
              View Logs
            </Link>
            <Link to="/brew/new" style={{ color: 'var(--accent-terracotta)' }} className="font-medium hover:opacity-80 transition-opacity">
              Log a Brew
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-4xl mx-auto px-8 py-24 text-center">
        <Coffee size={48} style={{ color: 'var(--accent-terracotta)' }} className="mx-auto mb-6" strokeWidth={2} />

        <h1 style={{ color: 'var(--primary-dark)' }} className="mb-4">
          BrewLog
        </h1>

        <p className="text-base font-medium" style={{ color: 'var(--accent-terracotta)' }}>
          Your coffee journal.
        </p>

        <div className="w-24 h-px mx-auto my-8" style={{ backgroundColor: 'var(--border-color)' }} />

        <p className="text-sm max-w-lg mx-auto mb-12 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
          Track every brew with precision. Log beans, equipment, and roasters — dial in your grind with extraction
          feedback and build a searchable history of your coffee journey. All in one place.
        </p>

        <div className="flex items-center justify-center gap-4 mb-16">
          <Link
            to="/brews"
            className="px-8 py-3 rounded-lg hover:opacity-90 transition-colors text-base font-medium"
            style={{
              backgroundColor: 'var(--primary-brown)',
              color: '#FFFFFF'
            }}
          >
            View Brews
          </Link>
          <Link
            to="/brew/new"
            className="px-8 py-3 rounded-lg hover:opacity-90 transition-colors text-base font-medium border"
            style={{
              backgroundColor: 'var(--cream)',
              color: 'var(--primary-brown)',
              borderColor: 'var(--border-color)'
            }}
          >
            Log a Brew
          </Link>
        </div>

        {/* Feature Icons */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-3xl mx-auto">
          <div className="flex flex-col items-center">
            <Clock size={32} style={{ color: 'var(--accent-terracotta)' }} className="mb-3" />
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Guided brew timer
            </p>
          </div>
          <div className="flex flex-col items-center">
            <Target size={32} style={{ color: 'var(--accent-terracotta)' }} className="mb-3" />
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Grind dial-in
            </p>
          </div>
          <div className="flex flex-col items-center">
            <BarChart3 size={32} style={{ color: 'var(--accent-terracotta)' }} className="mb-3" />
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Brew statistics
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
