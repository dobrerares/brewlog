import { type FormEvent, useState } from 'react'
import { AlertCircle, Mail } from 'lucide-react'
import { Link } from 'react-router'
import { api } from '@/lib/api'
import { Logo } from '@/app/components/Logo'
import { ThemeToggle } from '@/app/components/ThemeToggle'

export default function PasswordResetRequest() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setMessage(null)
    setError(null)
    setSubmitting(true)
    try {
      await api('/api/v1/auth/password-reset/request', {
        method: 'POST',
        body: JSON.stringify({ email: email.trim() }),
      })
      setMessage('If that email is registered, a reset link will arrive shortly.')
    } catch {
      setError('Could not send a reset email. Try again in a moment.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-8" style={{ backgroundColor: 'var(--background)' }}>
      <div className="absolute top-4 right-8"><ThemeToggle /></div>
      <div className="w-full max-w-md animate-fadeIn">
        <div className="text-center mb-8"><Logo size="large" link={false} /></div>
        <div className="rounded-xl border p-8" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
          <h2 className="text-2xl mb-2" style={{ fontFamily: 'var(--font-heading)' }}>Reset password</h2>
          <p className="text-sm mb-6" style={{ color: 'var(--text-muted)' }}>
            Enter your email and BrewLog will send a reset link.
          </p>
          <form onSubmit={submit} className="space-y-5">
            <div>
              <label htmlFor="reset-email" className="block text-sm mb-2">
                Email
              </label>
              <input
                id="reset-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2"
                style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)', borderColor: 'var(--border-color)' }}
                autoComplete="email"
                required
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-white hover:opacity-90 disabled:opacity-60"
              style={{ backgroundColor: 'var(--primary-brown)' }}
            >
              <Mail size={18} />
              <span>{submitting ? 'Sending...' : 'Send reset link'}</span>
            </button>
          </form>
          {message && <p className="mt-4 text-sm" style={{ color: 'var(--green)' }}>{message}</p>}
          {error && (
            <div className="mt-4 flex items-center gap-1 text-sm" style={{ color: 'var(--red)' }}>
              <AlertCircle size={14} />
              <span>{error}</span>
            </div>
          )}
          <p className="mt-5 text-sm" style={{ color: 'var(--text-muted)' }}>
            <Link to="/login" className="underline">Back to login</Link>
            <span className="mx-2">|</span>
            <Link to="/password-reset/confirm" className="underline">Use a reset token</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
