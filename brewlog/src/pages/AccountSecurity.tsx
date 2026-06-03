import { useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import { api } from '@/lib/api'
import { Navbar } from '@/app/components/Navbar'
import { useAuth } from '@/hooks/useAuth'

type SetupResponse = {
  secret: string
  provisioning_uri: string
  dev_code?: string | null
}

type VerifyResponse = {
  backup_codes: string[]
}

export default function AccountSecurity() {
  const { user, refresh } = useAuth()
  const [setup, setSetup] = useState<SetupResponse | null>(null)
  const [code, setCode] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function startSetup() {
    setError(null)
    setMessage(null)
    const data = await api<SetupResponse>('/api/v1/auth/mfa/setup', { method: 'POST' })
    setSetup(data)
    setBackupCodes([])
  }

  async function verifySetup(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setMessage(null)
    try {
      const data = await api<VerifyResponse>('/api/v1/auth/mfa/verify-setup', {
        method: 'POST',
        body: JSON.stringify({ code: code.trim() }),
      })
      setBackupCodes(data.backup_codes)
      setMessage('MFA is enabled for this account.')
      await refresh()
    } catch {
      setError('The verification code was not accepted.')
    }
  }

  return (
    <>
      <Navbar type="app" />
      <main className="mx-auto max-w-3xl px-6 py-8">
        <div className="mb-6 flex items-center gap-3">
          <ShieldCheck size={26} style={{ color: 'var(--primary-brown)' }} />
          <h1>Account security</h1>
        </div>

        <section className="space-y-5">
          {user?.mfa_enabled ? (
            <div className="rounded-lg border p-4" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
              <div className="font-semibold" style={{ color: 'var(--green)' }}>MFA is enabled</div>
              <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Password login now requires a magic link plus an authenticator code. Backup codes can replace the authenticator code.</div>
            </div>
          ) : (
            <button
              onClick={startSetup}
              className="rounded-lg px-4 py-2 text-white"
              style={{ backgroundColor: 'var(--primary-brown)' }}
            >
              Set up MFA
            </button>
          )}

          {!user?.mfa_enabled && setup && (
            <form onSubmit={verifySetup} className="space-y-4 rounded-lg border p-4" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
              <div>
                <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Secret</div>
                <div className="font-mono text-sm break-all">{setup.secret}</div>
              </div>
              <div>
                <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Provisioning URI</div>
                <div className="font-mono text-xs break-all">{setup.provisioning_uri}</div>
              </div>
              {setup.dev_code && (
                <div>
                  <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Current demo code</div>
                  <div className="font-mono text-lg">{setup.dev_code}</div>
                </div>
              )}
              <div>
                <label htmlFor="setup-code" className="block mb-2">Verification code</label>
                <input
                  id="setup-code"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full rounded-lg border px-4 py-2"
                  style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)', borderColor: 'var(--border-color)' }}
                  required
                />
              </div>
              <button className="rounded-lg px-4 py-2 text-white" style={{ backgroundColor: 'var(--primary-brown)' }}>
                Enable MFA
              </button>
            </form>
          )}

          {message && <p className="text-sm" style={{ color: 'var(--green)' }}>{message}</p>}
          {error && <p className="text-sm" style={{ color: 'var(--red)' }}>{error}</p>}

          {backupCodes.length > 0 && (
            <div className="rounded-lg border p-4" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
              <h2 className="mb-3">Backup codes</h2>
              <p className="mb-3 text-sm" style={{ color: 'var(--text-muted)' }}>Use these only if you cannot access your authenticator app. Each backup code works once.</p>
              <div className="grid grid-cols-2 gap-2 font-mono text-sm">
                {backupCodes.map((item) => <div key={item}>{item}</div>)}
              </div>
            </div>
          )}
        </section>
      </main>
    </>
  )
}
