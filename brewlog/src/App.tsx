import { BrowserRouter as Router, Routes, Route } from 'react-router'
import { Landing } from './app/pages/Landing'
import { Login } from './app/pages/Login'
import { Register } from './app/pages/Register'
import { BrewList } from './app/pages/BrewList'
import { BrewDetail } from './app/pages/BrewDetail'
import { BrewForm } from './app/pages/BrewForm'
import { Statistics } from './app/pages/Statistics'
import { CookieConsent } from './app/components/CookieConsent'
import './index.css'

export function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/brews" element={<BrewList />} />
        <Route path="/brew/new" element={<BrewForm />} />
        <Route path="/brew/:id" element={<BrewDetail />} />
        <Route path="/brew/:id/edit" element={<BrewForm />} />
        <Route path="/dashboard" element={<Statistics />} />
      </Routes>
      <CookieConsent />
    </Router>
  )
}

export default App
