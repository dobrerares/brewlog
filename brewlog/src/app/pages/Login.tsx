import { Link, useNavigate } from 'react-router'
import { AlertCircle } from 'lucide-react'
import { useState } from 'react'
import { Logo } from '../components/Logo'
import { ThemeToggle } from '../components/ThemeToggle'
import { useAuth } from '../hooks/useAuth'
import { useActivityTracker } from '../hooks/useActivityTracker'
import { useEffect } from 'react'

interface FormErrors {
  email?: string
  password?: string
}

function ErrorMessage({ message }: { message?: string }) {
  if (!message) return null
  return (
    <div className="flex items-center gap-1 mt-1 text-xs text-red-600">
      <AlertCircle size={12} />
      <span>{message}</span>
    </div>
  )
}

export function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const { trackVisit } = useActivityTracker()
  useEffect(() => { trackVisit('/login') }, [trackVisit])

  const [formValues, setFormValues] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState<FormErrors>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  const validateField = (name: string, value: string): string | undefined => {
    switch (name) {
      case 'email':
        if (!value) return 'Email is required'
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Please enter a valid email address'
        return undefined
      case 'password':
        if (!value) return 'Password is required'
        if (value.length < 6) return 'Password must be at least 6 characters'
        return undefined
      default:
        return undefined
    }
  }

  const handleFieldChange = (name: string, value: string) => {
    setFormValues(prev => ({ ...prev, [name]: value }))
    if (touched[name]) {
      const error = validateField(name, value)
      setErrors(prev => ({ ...prev, [name]: error }))
    }
  }

  const handleBlur = (name: string) => {
    setTouched(prev => ({ ...prev, [name]: true }))
    const error = validateField(name, formValues[name as keyof typeof formValues])
    setErrors(prev => ({ ...prev, [name]: error }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const newErrors: FormErrors = {}
    ;(['email', 'password'] as const).forEach(field => {
      const error = validateField(field, formValues[field])
      if (error) newErrors[field] = error
    })
    setErrors(newErrors)
    setTouched({ email: true, password: true })
    if (Object.keys(newErrors).length > 0) return

    try {
      const result = await login(formValues.email, formValues.password)
      if (result.mfaRequired) {
        navigate('/login/mfa', { state: { devMagicLink: result.devMagicLink } })
        return
      }
      navigate('/brews')
    } catch {
      setErrors({ password: 'Invalid credentials' })
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
          <h2 className="text-2xl mb-2" style={{ fontFamily: 'var(--font-heading)' }}>
            Welcome back
          </h2>
          <p className="text-sm mb-6" style={{ color: 'var(--text-muted)' }}>
            Log in to continue brewing.
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>
                Email <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                id="email"
                placeholder="you@example.com"
                value={formValues.email}
                onChange={(e) => handleFieldChange('email', e.target.value)}
                onBlur={() => handleBlur('email')}
                className={`w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                  touched.email && errors.email ? 'border-red-500' : ''
                }`}
                style={{
                  backgroundColor: 'var(--background)',
                  color: 'var(--foreground)',
                  borderColor: touched.email && errors.email ? undefined : 'var(--border-color)',
                  // @ts-expect-error CSS custom property for focus ring
                  '--tw-ring-color': 'var(--primary-brown)'
                }}
              />
              <ErrorMessage message={touched.email ? errors.email : undefined} />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>
                Password <span className="text-red-500">*</span>
              </label>
              <input
                type="password"
                id="password"
                placeholder="••••••••"
                value={formValues.password}
                onChange={(e) => handleFieldChange('password', e.target.value)}
                onBlur={() => handleBlur('password')}
                className={`w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                  touched.password && errors.password ? 'border-red-500' : ''
                }`}
                style={{
                  backgroundColor: 'var(--background)',
                  color: 'var(--foreground)',
                  borderColor: touched.password && errors.password ? undefined : 'var(--border-color)',
                  // @ts-expect-error CSS custom property
                  '--tw-ring-color': 'var(--primary-brown)'
                }}
              />
              <ErrorMessage message={touched.password ? errors.password : undefined} />
            </div>

            <button
              type="submit"
              className="w-full px-6 py-3 text-white rounded-lg hover:opacity-90 transition-colors font-medium"
              style={{ backgroundColor: 'var(--primary-brown)' }}
            >
              Log in
            </button>
          </form>
        </div>

        <p className="text-center mt-6 text-sm" style={{ color: 'var(--text-muted)' }}>
          Don't have an account?{' '}
          <Link to="/register" className="font-medium hover:underline" style={{ color: 'var(--primary-brown)' }}>
            Sign up
          </Link>
        </p>
        <p className="text-center mt-3 text-sm" style={{ color: 'var(--text-muted)' }}>
          Forgot your password?{' '}
          <Link to="/password-reset" className="font-medium hover:underline" style={{ color: 'var(--primary-brown)' }}>
            Get a reset link
          </Link>
        </p>
      </div>
    </div>
  )
}
