import { useEffect, useState } from 'react'
import { Navbar } from '@/app/components/Navbar'
import { api } from '@/lib/api'

type ResetResponse = {
  token: string
  expires_at: string
}

type AdminUser = {
  id: string
  email: string
  roles: string[]
  mfa_enabled: boolean
  is_observed: boolean
}

type DemoResponse = {
  users: number
  roasters: number
  beans: number
  equipment: number
  brewlogs: number
}

type AnalysisResponse = {
  user_id: string
  risk: string
  observed: boolean
  reason: string
  source: string
}

export default function SecurityTools() {
  const [resetUserId, setResetUserId] = useState('')
  const [users, setUsers] = useState<AdminUser[]>([])
  const [userFilter, setUserFilter] = useState('')
  const [reset, setReset] = useState<ResetResponse | null>(null)
  const [analyzeUserId, setAnalyzeUserId] = useState('')
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)
  const [demo, setDemo] = useState<DemoResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function loadUsers(query = '') {
    const params = new URLSearchParams()
    if (query) params.set('q', query)
    const data = await api<AdminUser[]>(`/api/v1/admin/users?${params}`)
    setUsers(data)
    if (!resetUserId && data.length > 0) setResetUserId(data[0].id)
  }

  useEffect(() => {
    loadUsers().catch(() => setError('Could not load users.'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function issueReset(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setReset(null)
    try {
      const data = await api<ResetResponse>(`/api/v1/admin/users/${resetUserId.trim()}/password-reset`, { method: 'POST' })
      setReset(data)
    } catch {
      setError('Could not issue reset token for that user.')
    }
  }

  async function analyze(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setAnalysis(null)
    try {
      const data = await api<AnalysisResponse>(`/api/v1/admin/security/analyze-user/${analyzeUserId.trim()}`, { method: 'POST' })
      setAnalysis(data)
    } catch {
      setError('Could not analyze that user.')
    }
  }

  async function generateDemo() {
    setError(null)
    setDemo(null)
    try {
      const data = await api<DemoResponse>('/api/v1/admin/demo-data/generate', {
        method: 'POST',
        body: JSON.stringify({ users: 3, brewlogs_per_user: 5 }),
      })
      setDemo(data)
    } catch {
      setError('Demo data generation failed.')
    }
  }

  return (
    <>
      <Navbar type="app" />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <h1 className="mb-6">Security tools</h1>
        <div className="grid gap-5 md:grid-cols-2">
          <section className="rounded-lg border p-4" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
            <h2 className="mb-4">Password reset</h2>
            <div className="mb-4 flex gap-2">
              <input
                value={userFilter}
                onChange={(e) => setUserFilter(e.target.value)}
                placeholder="filter by email"
                className="min-w-0 flex-1 rounded-lg border px-3 py-2 text-sm"
                style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)', borderColor: 'var(--border-color)' }}
              />
              <button
                type="button"
                onClick={() => loadUsers(userFilter).catch(() => setError('Could not load users.'))}
                className="rounded-lg px-3 py-2 text-white"
                style={{ backgroundColor: 'var(--primary-brown)' }}
              >
                Search
              </button>
            </div>
            <form onSubmit={issueReset} className="space-y-3">
              <select
                value={resetUserId}
                onChange={(e) => setResetUserId(e.target.value)}
                className="w-full rounded-lg border px-3 py-2 text-sm"
                style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)', borderColor: 'var(--border-color)' }}
              >
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.email} ({user.roles.join(', ') || 'no role'})
                  </option>
                ))}
              </select>
              <input
                value={resetUserId}
                onChange={(e) => setResetUserId(e.target.value)}
                placeholder="user id"
                className="w-full rounded-lg border px-3 py-2 font-mono text-sm"
                style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)', borderColor: 'var(--border-color)' }}
                required
              />
              <button className="rounded-lg px-4 py-2 text-white" style={{ backgroundColor: 'var(--primary-brown)' }}>
                Issue reset
              </button>
            </form>
            {reset && (
              <div className="mt-4 text-sm">
                <div style={{ color: 'var(--text-muted)' }}>Token</div>
                <div className="break-all font-mono">{reset.token}</div>
                <div className="mt-2" style={{ color: 'var(--text-muted)' }}>Expires {new Date(reset.expires_at).toLocaleString()}</div>
              </div>
            )}
          </section>

          <section className="rounded-lg border p-4" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
            <h2 className="mb-4">Suspicious behavior</h2>
            <form onSubmit={analyze} className="space-y-3">
              <input
                value={analyzeUserId}
                onChange={(e) => setAnalyzeUserId(e.target.value)}
                placeholder="user id"
                className="w-full rounded-lg border px-3 py-2 font-mono text-sm"
                style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)', borderColor: 'var(--border-color)' }}
                required
              />
              <button className="rounded-lg px-4 py-2 text-white" style={{ backgroundColor: 'var(--primary-brown)' }}>
                Analyze
              </button>
            </form>
            {analysis && (
              <div className="mt-4 text-sm">
                <div>Risk: <span className="font-semibold">{analysis.risk}</span></div>
                <div>Observed: {analysis.observed ? 'yes' : 'no'}</div>
                <div>Source: {analysis.source}</div>
                <div className="mt-2" style={{ color: 'var(--text-muted)' }}>{analysis.reason}</div>
              </div>
            )}
          </section>

          <section className="rounded-lg border p-4 md:col-span-2" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
            <h2 className="mb-4">Demo data</h2>
            <button onClick={generateDemo} className="rounded-lg px-4 py-2 text-white" style={{ backgroundColor: 'var(--primary-brown)' }}>
              Generate small demo dataset
            </button>
            {demo && (
              <div className="mt-4 grid grid-cols-2 gap-3 text-sm md:grid-cols-5">
                {Object.entries(demo).map(([key, value]) => (
                  <div key={key}>
                    <div style={{ color: 'var(--text-muted)' }}>{key}</div>
                    <div className="text-lg font-semibold">{value}</div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
        {error && <p className="mt-5 text-sm" style={{ color: 'var(--red)' }}>{error}</p>}
      </main>
    </>
  )
}
