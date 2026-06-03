import { useAuth as useBackendAuth } from '@/hooks/useAuth'

export function useAuth() {
  const auth = useBackendAuth()

  return {
    ...auth,
    isAuthenticated: auth.state.status === 'auth',
    login: auth.login,
    verifyMfaLogin: auth.verifyMfaLogin,
    resendLoginEmailCode: auth.resendLoginEmailCode,
    register: (_name: string, email: string, password: string) => auth.register(email, password),
  }
}
