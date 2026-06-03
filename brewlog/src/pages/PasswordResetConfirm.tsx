import { useState } from 'react'
import { Link } from 'react-router'
import { api } from '@/lib/api'
import { Logo } from '@/app/components/Logo'
import { ThemeToggle } from '@/app/components/ThemeToggle'

export default function PasswordResetConfirm() {
  const [token, setToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setMessage(null)
    setError(null)
    try {
      await api('/api/v1/auth/password-reset/confirm', {
        method: 'POST',
        body: JSON.stringify({ token: token.trim(), new_password: newPassword }),
      })
      setMessage('Password changed. You can now log in with the new password.')
      setToken('')
      setNewPassword('')
    } catch {
      setError('The reset token is invalid, expired, or already used.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-8" style={{ backgroundColor: 'var(--background)' }}>
      <div className="absolute top-4 right-8"><ThemeToggle /></div>
      <div className="w-full max-w-md animate-fadeIn">
        <div className="text-center mb-8"><Logo size="large" link={false} /></div>
        <div className="rounded-xl border p-8" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
          <h2 className="text-2xl mb-6" style={{ fontFamily: 'var(--font-heading)' }}>Reset password</h2>
          <form onSubmit={submit} className="space-y-5">
            <div>
              <label htmlFor="reset-token" className="block mb-2">Reset token</label>
              <input
                id="reset-token"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                className="w-full rounded-lg border px-4 py-2"
                style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)', borderColor: 'var(--border-color)' }}
                required
              />
            </div>
            <div>
              <label htmlFor="new-password" className="block mb-2">New password</label>
              <input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-lg border px-4 py-2"
                style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)', borderColor: 'var(--border-color)' }}
                minLength={6}
                required
              />
            </div>
            <button className="w-full rounded-lg px-4 py-2 text-white" style={{ backgroundColor: 'var(--primary-brown)' }}>
              Change password
            </button>
          </form>
          {message && <p className="mt-4 text-sm" style={{ color: 'var(--green)' }}>{message}</p>}
          {error && <p className="mt-4 text-sm" style={{ color: 'var(--red)' }}>{error}</p>}
          <p className="mt-5 text-sm" style={{ color: 'var(--text-muted)' }}>
            <Link to="/login" className="underline">Back to login</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
