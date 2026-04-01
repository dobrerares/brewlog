import { useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation, useNavigationType } from 'react-router'
import { Landing } from './app/pages/Landing'
import { Login } from './app/pages/Login'
import { Register } from './app/pages/Register'
import { BrewList } from './app/pages/BrewList'
import { BrewDetail } from './app/pages/BrewDetail'
import { BrewForm } from './app/pages/BrewForm'
import { Statistics } from './app/pages/Statistics'
import { CookieConsent } from './app/components/CookieConsent'
import './index.css'

function AnimatedRoutes() {
  const location = useLocation()
  const navigationType = useNavigationType()
  const [displayLocation, setDisplayLocation] = useState(location)
  const [transitionStage, setTransitionStage] = useState<'page-enter' | 'page-exit'>('page-enter')
  const [transitionDirection, setTransitionDirection] = useState<'forward' | 'back'>('forward')

  useEffect(() => {
    const current = `${location.pathname}${location.search}${location.hash}`
    const displayed = `${displayLocation.pathname}${displayLocation.search}${displayLocation.hash}`

    if (current !== displayed) {
      setTransitionDirection(navigationType === 'POP' ? 'back' : 'forward')
      setTransitionStage('page-exit')
      const timeoutId = window.setTimeout(() => {
        setDisplayLocation(location)
        setTransitionStage('page-enter')
      }, 160)

      return () => window.clearTimeout(timeoutId)
    }
  }, [location, displayLocation, navigationType])

  return (
    <div className={`route-shell ${transitionStage} direction-${transitionDirection}`}>
      <Routes location={displayLocation}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/brews" element={<BrewList />} />
        <Route path="/brew/new" element={<BrewForm />} />
        <Route path="/brew/:id" element={<BrewDetail />} />
        <Route path="/brew/:id/edit" element={<BrewForm />} />
        <Route path="/dashboard" element={<Statistics />} />
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
