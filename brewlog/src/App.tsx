import { BrowserRouter as Router, Routes, Route } from 'react-router'
import { Landing } from './app/pages/Landing'
import { BrewList } from './app/pages/BrewList'
import { BrewDetail } from './app/pages/BrewDetail'
import { BrewForm } from './app/pages/BrewForm'
import { CookieConsent } from './app/components/CookieConsent'
import './index.css'

export function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/brews" element={<BrewList />} />
        <Route path="/brew/new" element={<BrewForm />} />
        <Route path="/brew/:id" element={<BrewDetail />} />
        <Route path="/brew/:id/edit" element={<BrewForm />} />
      </Routes>
      <CookieConsent />
    </Router>
  )
}

export default App
