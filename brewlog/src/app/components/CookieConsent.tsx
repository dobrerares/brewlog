import { useCookie } from '../hooks/useCookie'

export function CookieConsent() {
  const [consent, setConsent] = useCookie('brewlog_consent', '')

  if (consent === 'accepted') return null

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50 border-t px-6 py-4"
      style={{
        backgroundColor: 'var(--card)',
        borderColor: 'var(--border-color)',
      }}
    >
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          We use cookies to remember your preferences and track activity to improve your experience.
        </p>
        <button
          onClick={() => setConsent('accepted')}
          className="px-6 py-2 rounded-lg text-sm font-medium text-white shrink-0 hover:opacity-90 transition-opacity"
          style={{ backgroundColor: 'var(--primary-brown)' }}
        >
          Accept
        </button>
      </div>
    </div>
  )
}
