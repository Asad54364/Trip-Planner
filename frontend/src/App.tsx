import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import TripResultsPage from './pages/TripResultsPage'

export default function App() {
  return (
    <div className="min-h-screen">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/trips/:tripId" element={<TripResultsPage />} />
      </Routes>
    </div>
  )
}
