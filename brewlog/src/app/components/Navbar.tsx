import { Link, useLocation } from 'react-router'
import { Logo } from './Logo'
import { ThemeToggle } from './ThemeToggle'
import { useAuth } from '../hooks/useAuth'
import { Menu, X } from 'lucide-react'
import { useState } from 'react'

interface NavbarProps {
  type?: 'landing' | 'app'
}

export function Navbar({ type = 'landing' }: NavbarProps) {
  const location = useLocation()
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)

  const isActive = (path: string) => {
    if (path === '/brews') return location.pathname === '/brews' || location.pathname.startsWith('/brew')
    return location.pathname === path
  }

  const navLinkClass = (path: string) =>
    `text-sm transition-colors ${
      isActive(path)
        ? 'font-semibold border-b-2'
        : 'hover:opacity-70'
    }`

  if (type === 'landing') {
    return (
      <nav style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--card)' }} className="border-b">
        <div className="max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
          <Logo size="small" link={false} />
          <div className="flex items-center gap-4">
            <Link
              to="/login"
              className="px-4 py-2 rounded-lg transition-colors"
              style={{ color: 'var(--primary-brown)' }}
            >
              Log in
            </Link>
            <Link
              to="/register"
              className="px-4 py-2 text-white rounded-lg hover:opacity-90 transition-colors"
              style={{ backgroundColor: 'var(--primary-brown)' }}
            >
              Sign up
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </nav>
    )
  }

  const navLinks = [
    { path: '/brews', label: 'Brew Logs' },
    { path: '/live', label: 'Live' },
    { path: '/dashboard', label: 'Dashboard' },
  ]

  return (
    <nav style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--card)' }} className="border-b">
      <div className="max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
        <Logo size="small" />

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map(({ path, label }) => (
            <Link
              key={path}
              to={path}
              className={navLinkClass(path)}
              style={{
                color: isActive(path) ? 'var(--primary-brown)' : 'var(--text-muted)',
                borderColor: isActive(path) ? 'var(--primary-brown)' : 'transparent'
              }}
            >
              {label}
            </Link>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-4">
          <ThemeToggle />
          <button
            onClick={logout}
            className="w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-colors hover:opacity-80"
            style={{ backgroundColor: 'var(--cream)', color: 'var(--primary-brown)' }}
            title={`Logged in as ${user?.name || 'User'} — click to log out`}
          >
            {(user?.name || 'U')[0].toUpperCase()}
          </button>
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
          style={{ color: 'var(--foreground)' }}
        >
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t animate-slideDown" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--card)' }}>
          <div className="px-8 py-4 space-y-4">
            {navLinks.map(({ path, label }) => (
              <Link
                key={path}
                to={path}
                onClick={() => setMobileOpen(false)}
                className="block text-sm py-2"
                style={{ color: isActive(path) ? 'var(--primary-brown)' : 'var(--text-muted)' }}
              >
                {label}
              </Link>
            ))}
            <div className="flex items-center gap-4 pt-2 border-t" style={{ borderColor: 'var(--border-color)' }}>
              <ThemeToggle />
              <button
                onClick={logout}
                className="text-sm"
                style={{ color: 'var(--red)' }}
              >
                Log out
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}
