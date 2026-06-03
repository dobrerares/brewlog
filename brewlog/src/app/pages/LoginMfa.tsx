import { AlertCircle, Mail, ShieldCheck } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router'
import { Logo } from '../components/Logo'
import { ThemeToggle } from '../components/ThemeToggle'
import { useAuth } from '../hooks/useAuth'

export function LoginMfa() {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const { verifyMfaLogin, resendLoginEmailCode } = useAuth()
  const emailToken = searchParams.get('token') ?? ''
  const [totpCode, setTotpCode] = useState('')
  const [devMagicLink, setDevMagicLink] = useState<string | null>(
    (location.state as { devMagicLink?: string | null } | null)?.devMagicLink ?? null,
  )
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [resending, setResending] = useState(false)
  const hasMagicLink = emailToken.length > 0
  const devToken = useMemo(() => {
    if (!devMagicLink) return ''
    try {
      return new URL(devMagicLink).searchParams.get('token') ?? ''
    } catch {
      return ''
    }
  }, [devMagicLink])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await verifyMfaLogin(totpCode.trim(), emailToken || devToken)
      navigate('/brews')
    } catch (err) {
      const message = err instanceof Error ? err.message : ''
      if (message.includes('mfa challenge missing')) {
        setError('Verification session expired. Log in again before opening the email link.')
      } else {
        setError('Invalid or expired verification factors')
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function handleResend() {
    setError(null)
    setResending(true)
    try {
      const result = await resendLoginEmailCode()
      setDevMagicLink(result.dev_magic_link ?? null)
    } catch {
      setError('Could not resend the magic link. Log in again and retry.')
    } finally {
      setResending(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-8" style={{ backgroundColor: 'var(--background)' }}>
      <div className="absolute top-4 right-8">
        <ThemeToggle />
      </div>
      <div className="w-full max-w-md animate-fadeIn">
        <div className="text-center mb-8">
          <Logo size="large" link={false} />
        </div>
        <div className="rounded-xl border p-8" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
          <div className="mb-5 flex items-center gap-3">
            <ShieldCheck size={24} style={{ color: 'var(--primary-brown)' }} />
            <h2 className="text-2xl" style={{ fontFamily: 'var(--font-heading)' }}>Verification</h2>
          </div>
          <div className="mb-5 rounded-lg border p-3" style={{ borderColor: 'var(--border-color)' }}>
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm">
                <Mail size={16} style={{ color: hasMagicLink || devToken ? 'var(--green)' : 'var(--text-muted)' }} />
                <span>{hasMagicLink || devToken ? 'Magic link ready' : 'Open the magic link sent to your email'}</span>
              </div>
              <button
                type="button"
                onClick={handleResend}
                disabled={resending}
                className="text-sm font-medium hover:underline disabled:opacity-60"
                style={{ color: 'var(--primary-brown)' }}
              >
                {resending ? 'Sending...' : 'Resend'}
              </button>
            </div>
            {devMagicLink && (
              <a className="mt-2 block break-all text-xs underline" href={devMagicLink} style={{ color: 'var(--text-muted)' }}>
                Demo magic link
              </a>
            )}
          </div>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="mfa-code" className="block text-sm mb-2">
                Authenticator or backup code
              </label>
              <input
                id="mfa-code"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                className="w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2"
                style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)', borderColor: 'var(--border-color)' }}
                autoComplete="one-time-code"
                inputMode="numeric"
                required
              />
              {error && (
                <div className="flex items-center gap-1 mt-2 text-xs text-red-600">
                  <AlertCircle size={12} />
                  <span>{error}</span>
                </div>
              )}
            </div>
            <button
              type="submit"
              disabled={submitting || (!hasMagicLink && !devToken)}
              className="w-full px-6 py-3 text-white rounded-lg hover:opacity-90 disabled:opacity-60"
              style={{ backgroundColor: 'var(--primary-brown)' }}
            >
              Verify
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
