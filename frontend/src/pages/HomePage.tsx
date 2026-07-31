import TripForm from '../components/TripForm'

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="py-6 px-8 border-b border-white/5">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-blue-500/20">
            T
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">
              Trip Planner & ELD
            </h1>
            <p className="text-xs text-slate-400 tracking-wide">
              FMCSA-Compliant HOS Log Generator
            </p>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-2xl animate-fade-in">
          {/* Hero text */}
          <div className="text-center mb-10">
            <h2 className="text-4xl font-extrabold text-white mb-3 tracking-tight leading-tight">
              Plan Your Route,<br />
              <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                Generate Your Logs
              </span>
            </h2>
            <p className="text-slate-400 text-lg max-w-md mx-auto">
              Enter your trip details and get FMCSA-compliant daily log sheets
              with accurate HOS scheduling, instantly.
            </p>
          </div>

          {/* Form card */}
          <div className="glass-card p-8 animate-pulse-glow">
            <TripForm />
          </div>

          {/* Assumptions footer */}
          <div className="mt-6 text-center">
            <details className="inline-block text-sm text-slate-500">
              <summary className="cursor-pointer hover:text-slate-300 transition-colors">
                ⓘ HOS Assumptions Used
              </summary>
              <div className="mt-3 text-left glass-card p-4 text-xs text-slate-400 space-y-1">
                <p>• Property-carrying driver, <strong>70-hour / 8-day</strong> cycle</p>
                <p>• No adverse driving conditions exception</p>
                <p>• Refueling at least once every <strong>1,000 miles</strong></p>
                <p>• <strong>1 hour</strong> each for pickup and drop-off</p>
                <p>• 11-hour driving limit, 14-hour window, 30-minute break after 8 hrs</p>
                <p>• 10-hour consecutive off-duty reset, 34-hour cycle restart</p>
                <p className="text-slate-500 pt-1 border-t border-white/5">
                  Rolling 70-hr total resets only via 34-hr restart (simplified — see README)
                </p>
              </div>
            </details>
          </div>
        </div>
      </main>
    </div>
  )
}
