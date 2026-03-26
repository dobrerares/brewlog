import { useCookie } from './useCookie'
import { useNavigate } from 'react-router'

interface User {
  name: string
  email: string
}

export function useAuth() {
  const [user, setUser] = useCookie<User | null>('brewlog_user', null)
  const navigate = useNavigate()

  const login = (email: string, _password: string) => {
    // Fake auth — accept any valid-looking credentials
    const name = email.split('@')[0]
    setUser({ name, email })
  }

  const register = (name: string, email: string, _password: string) => {
    setUser({ name, email })
  }

  const logout = () => {
    setUser(null)
    navigate('/login')
  }

  const isAuthenticated = !!user

  return { user, login, register, logout, isAuthenticated }
}
