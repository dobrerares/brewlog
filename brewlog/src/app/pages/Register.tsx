import { Link, useNavigate } from 'react-router'
import { AlertCircle } from 'lucide-react'
import { useState, useEffect } from 'react'
import { Logo } from '../components/Logo'
import { ThemeToggle } from '../components/ThemeToggle'
import { useAuth } from '../hooks/useAuth'
import { useActivityTracker } from '../hooks/useActivityTracker'

interface FormErrors {
  name?: string
  email?: string
  password?: string
  confirmPassword?: string
  form?: string
}

export function Register() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const { trackVisit } = useActivityTracker()
  useEffect(() => { trackVisit('/register') }, [])

  const [formValues, setFormValues] = useState({
    name: '', email: '', password: '', confirmPassword: ''
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  const validateField = (name: string, value: string): string | undefined => {
    switch (name) {
      case 'name':
        if (!value) return 'Name is required'
        if (value.length < 2) return 'Name must be at least 2 characters'
        return undefined
      case 'email':
        if (!value) return 'Email is required'
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Please enter a valid email address'
        return undefined
      case 'password':
        if (!value) return 'Password is required'
        if (value.length < 8) return 'Password must be at least 8 characters'
        if (!/[A-Z]/.test(value)) return 'Password must contain at least one uppercase letter'
        if (!/[a-z]/.test(value)) return 'Password must contain at least one lowercase letter'
        if (!/[0-9]/.test(value)) return 'Password must contain at least one number'
        return undefined
      case 'confirmPassword':
        if (!value) return 'Please confirm your password'
        if (value !== formValues.password) return 'Passwords do not match'
        return undefined
      default:
        return undefined
    }
  }

  const handleFieldChange = (name: string, value: string) => {
    setFormValues(prev => ({ ...prev, [name]: value }))
    if (touched[name]) {
      setErrors(prev => ({ ...prev, [name]: validateField(name, value) }))
    }
    if (name === 'password' && touched.confirmPassword) {
      const confirmError = formValues.confirmPassword !== value ? 'Passwords do not match' : undefined
      setErrors(prev => ({ ...prev, confirmPassword: confirmError }))
    }
  }

  const handleBlur = (name: string) => {
    setTouched(prev => ({ ...prev, [name]: true }))
    setErrors(prev => ({ ...prev, [name]: validateField(name, formValues[name as keyof typeof formValues]) }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const newErrors: FormErrors = {}
    const fields = ['name', 'email', 'password', 'confirmPassword'] as const
    fields.forEach(field => {
      const error = validateField(field, formValues[field])
      if (error) newErrors[field] = error
    })
    setErrors(newErrors)
    const allTouched: Record<string, boolean> = {}
    fields.forEach(f => { allTouched[f] = true })
    setTouched(allTouched)
    if (Object.keys(newErrors).length > 0) return

    try {
      await register(formValues.name, formValues.email, formValues.password)
      navigate('/brews')
    } catch (err) {
      const error = err as Error & { status?: number }
      if (error.status === 409) {
        setErrors({ email: 'Email already registered' })
        return
      }
      if (error.status === 422) {
        setErrors({ form: 'Registration data was rejected by the server.' })
        return
      }
      setErrors({ form: error.message || 'Could not reach the registration server.' })
    }
  }

  const getPasswordStrength = (password: string) => {
    if (!password) return { strength: 0, label: '', color: '' }
    let s = 0
    if (password.length >= 8) s++
    if (/[A-Z]/.test(password)) s++
    if (/[a-z]/.test(password)) s++
    if (/[0-9]/.test(password)) s++
    if (/[^A-Za-z0-9]/.test(password)) s++
    if (s <= 2) return { strength: 33, label: 'Weak', color: 'var(--red)' }
    if (s <= 3) return { strength: 66, label: 'Medium', color: 'var(--yellow)' }
    return { strength: 100, label: 'Strong', color: 'var(--green)' }
  }

  const passwordStrength = getPasswordStrength(formValues.password)

  const ErrorMessage = ({ message }: { message?: string }) => {
    if (!message) return null
    return (
      <div className="flex items-center gap-1 mt-1 text-xs text-red-600">
        <AlertCircle size={12} />
        <span>{message}</span>
      </div>
    )
  }

  const inputStyle = (field: string) => ({
    backgroundColor: 'var(--background)',
    color: 'var(--foreground)',
    borderColor: touched[field] && errors[field as keyof FormErrors] ? undefined : 'var(--border-color)'
  })

  return (
    <div className="min-h-screen flex items-center justify-center px-8 py-12" style={{ backgroundColor: 'var(--background)' }}>
      <div className="absolute top-4 right-8">
        <ThemeToggle />
      </div>
      <div className="w-full max-w-md animate-fadeIn">
        <div className="text-center mb-8">
          <Logo size="large" link={false} />
        </div>

        <div className="rounded-xl border p-8" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border-color)' }}>
          <h2 className="text-2xl mb-2" style={{ fontFamily: 'var(--font-heading)' }}>
            Create account
          </h2>
          <p className="text-sm mb-6" style={{ color: 'var(--text-muted)' }}>
            Start tracking your coffee journey.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="name" className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>
                Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text" id="name" placeholder="Your name"
                value={formValues.name}
                onChange={(e) => handleFieldChange('name', e.target.value)}
                onBlur={() => handleBlur('name')}
                className={`w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${touched.name && errors.name ? 'border-red-500' : ''}`}
                style={inputStyle('name')}
              />
              <ErrorMessage message={touched.name ? errors.name : undefined} />
            </div>

            <div>
              <label htmlFor="reg-email" className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>
                Email <span className="text-red-500">*</span>
              </label>
              <input
                type="email" id="reg-email" placeholder="you@example.com"
                value={formValues.email}
                onChange={(e) => handleFieldChange('email', e.target.value)}
                onBlur={() => handleBlur('email')}
                className={`w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${touched.email && errors.email ? 'border-red-500' : ''}`}
                style={inputStyle('email')}
              />
              <ErrorMessage message={touched.email ? errors.email : undefined} />
            </div>

            <div>
              <label htmlFor="reg-password" className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>
                Password <span className="text-red-500">*</span>
              </label>
              <input
                type="password" id="reg-password" placeholder="••••••••"
                value={formValues.password}
                onChange={(e) => handleFieldChange('password', e.target.value)}
                onBlur={() => handleBlur('password')}
                className={`w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${touched.password && errors.password ? 'border-red-500' : ''}`}
                style={inputStyle('password')}
              />
              {formValues.password && (
                <div className="mt-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Password strength:</span>
                    <span className="text-xs font-medium" style={{ color: passwordStrength.color }}>
                      {passwordStrength.label}
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--border-color)' }}>
                    <div
                      className="h-full transition-all duration-300 rounded-full"
                      style={{ width: `${passwordStrength.strength}%`, backgroundColor: passwordStrength.color }}
                    />
                  </div>
                </div>
              )}
              <ErrorMessage message={touched.password ? errors.password : undefined} />
            </div>

            <div>
              <label htmlFor="confirm-password" className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>
                Confirm password <span className="text-red-500">*</span>
              </label>
              <input
                type="password" id="confirm-password" placeholder="••••••••"
                value={formValues.confirmPassword}
                onChange={(e) => handleFieldChange('confirmPassword', e.target.value)}
                onBlur={() => handleBlur('confirmPassword')}
                className={`w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${touched.confirmPassword && errors.confirmPassword ? 'border-red-500' : ''}`}
                style={inputStyle('confirmPassword')}
              />
              <ErrorMessage message={touched.confirmPassword ? errors.confirmPassword : undefined} />
            </div>

            <button
              type="submit"
              className="w-full px-6 py-3 text-white rounded-lg hover:opacity-90 transition-colors font-medium"
              style={{ backgroundColor: 'var(--primary-brown)' }}
            >
              Create account
            </button>
            <ErrorMessage message={errors.form} />
          </form>
        </div>

        <p className="text-center mt-6 text-sm" style={{ color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <Link to="/login" className="font-medium hover:underline" style={{ color: 'var(--primary-brown)' }}>
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}
