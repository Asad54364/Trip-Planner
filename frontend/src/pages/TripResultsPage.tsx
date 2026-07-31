import { useParams, Link } from 'react-router-dom'
import { useFetchTrip } from '../api/client'
import RouteMap from '../components/RouteMap'
import TripSummaryCard from '../components/TripSummaryCard'
import LogSheetSvg from '../components/LogSheetSvg'
import { useState } from 'react'

export default function TripResultsPage() {
  const { tripId } = useParams<{ tripId: string }>()
  const { data, isLoading, isError, error } = useFetchTrip(tripId)
  const [activeSheet, setActiveSheet] = useState(0)

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <div className="spinner mx-auto mb-4" style={{ width: 48, height: 48, borderWidth: 4 }} />
          <p className="text-slate-400 text-lg">Loading trip data…</p>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="glass-card p-8 max-w-md text-center animate-fade-in">
          <p className="text-red-400 text-4xl mb-3">⚠</p>
          <h2 className="text-xl font-bold text-white mb-2">Trip Not Found</h2>
          <p className="text-slate-400 mb-6">
            {(error as Error)?.message || 'Could not load trip data.'}
          </p>
          <Link to="/" className="btn-primary inline-block">← Plan a New Trip</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="py-4 px-6 border-b border-white/5 sticky top-0 z-50 bg-slate-900/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white font-bold text-sm">
              T
            </div>
            <span className="text-white font-semibold">Trip Planner & ELD</span>
          </Link>
          <Link to="/" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
            + New Trip
          </Link>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {/* Summary */}
        <div className="animate-fade-in">
          <TripSummaryCard
            summary={data.summary}
            driverInfo={data.driver_info}
            cycleUsed={data.log_sheets[data.log_sheets.length - 1]?.recap.cycle_hours_used_today || 0}
          />
        </div>

        {/* Map */}
        <div className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            🗺️ Route Map
          </h2>
          <div className="glass-card overflow-hidden" style={{ height: 420 }}>
            <RouteMap geometry={data.route.geometry} stops={data.route.stops} />
          </div>
        </div>

        {/* Log Sheets */}
        <div className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            📋 Daily Log Sheets
          </h2>

          {/* Day tabs */}
          {data.log_sheets.length > 1 && (
            <div className="flex gap-2 mb-4 flex-wrap">
              {data.log_sheets.map((sheet, idx) => (
                <button
                  key={sheet.day_index}
                  onClick={() => setActiveSheet(idx)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    activeSheet === idx
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                      : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
                  }`}
                >
                  Day {sheet.day_index} — {sheet.date}
                </button>
              ))}
            </div>
          )}

          {/* Active log sheet */}
          <div className="log-sheet-container">
            <LogSheetSvg
              sheet={data.log_sheets[activeSheet]}
              driverInfo={data.driver_info}
            />
          </div>
        </div>
      </main>
    </div>
  )
}
