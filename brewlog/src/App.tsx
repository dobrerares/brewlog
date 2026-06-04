import { BrowserRouter as Router, Routes, Route, useLocation, useNavigationType } from 'react-router'
import { Landing } from './app/pages/Landing'
import { Login } from './app/pages/Login'
import { LoginMfa } from './app/pages/LoginMfa'
import { Register } from './app/pages/Register'
import { BrewList } from './app/pages/BrewList'
import { BrewDetail } from './app/pages/BrewDetail'
import { BrewForm } from './app/pages/BrewForm'
import { Statistics } from './app/pages/Statistics'
import { LiveBrews } from './app/pages/LiveBrews'
import { CookieConsent } from './app/components/CookieConsent'
import ChatPage from '@/pages/Chat'
import ObservedUsers from '@/pages/admin/ObservedUsers'
import AuditLogExplorer from '@/pages/admin/AuditLogExplorer'
import SecurityTools from '@/pages/admin/SecurityTools'
import AccountSecurity from '@/pages/AccountSecurity'
import PasswordResetRequest from '@/pages/PasswordResetRequest'
import PasswordResetConfirm from '@/pages/PasswordResetConfirm'
import { RequireAuth } from '@/components/RequireAuth'
import { RequirePerm } from '@/components/RequirePerm'
import './index.css'

function AnimatedRoutes() {
  const location = useLocation()
  const navigationType = useNavigationType()
  const transitionDirection = navigationType === 'POP' ? 'back' : 'forward'

  return (
    <div
      key={location.key}
      className={`route-shell page-enter direction-${transitionDirection}`}
    >
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/login/mfa" element={<LoginMfa />} />
        <Route path="/register" element={<Register />} />
        <Route path="/password-reset" element={<PasswordResetRequest />} />
        <Route path="/password-reset/confirm" element={<PasswordResetConfirm />} />
        <Route path="/brews" element={<BrewList />} />
        <Route path="/brew/new" element={<BrewForm />} />
        <Route path="/brew/:id" element={<BrewDetail />} />
        <Route path="/brew/:id/edit" element={<BrewForm />} />
        <Route path="/dashboard" element={<Statistics />} />
        <Route path="/live" element={<LiveBrews />} />
        <Route path="/chat" element={<RequireAuth><ChatPage /></RequireAuth>} />
        <Route path="/account/security" element={<RequireAuth><AccountSecurity /></RequireAuth>} />
        <Route path="/admin/observed" element={<RequirePerm perm="user:observe"><ObservedUsers /></RequirePerm>} />
        <Route path="/admin/audit" element={<RequirePerm perm="log:read"><AuditLogExplorer /></RequirePerm>} />
        <Route path="/admin/security" element={<RequirePerm perm="user:reset"><SecurityTools /></RequirePerm>} />
      </Routes>
    </div>
  )
}

export function App() {
  return (
    <Router>
      <AnimatedRoutes />
      <CookieConsent />
    </Router>
  )
}

export default App
