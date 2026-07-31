interface Props {
  summary: {
    total_distance_miles: number
    total_driving_hours: number
    total_trip_duration_hours: number
    num_log_sheets: number
  }
  driverInfo: {
    driver_name: string
    carrier_name: string
    truck_number: string
  }
  cycleUsed: number
}

export default function TripSummaryCard({ summary, driverInfo, cycleUsed }: Props) {
  const hoursAvail = Math.max(0, 70 - cycleUsed)

  const stats = [
    { label: 'Total Distance', value: `${summary.total_distance_miles.toLocaleString()} mi`, icon: '🛣️' },
    { label: 'Driving Time', value: `${summary.total_driving_hours.toFixed(1)} hrs`, icon: '🚛' },
    { label: 'Trip Duration', value: `${summary.total_trip_duration_hours.toFixed(1)} hrs`, icon: '⏱️' },
    { label: 'Log Sheets', value: `${summary.num_log_sheets} day${summary.num_log_sheets > 1 ? 's' : ''}`, icon: '📋' },
    { label: 'Cycle Used', value: `${cycleUsed.toFixed(1)} / 70 hrs`, icon: '🔄' },
    { label: 'Hours Available', value: `${hoursAvail.toFixed(1)} hrs`, icon: '✅' },
  ]

  return (
    <div className="glass-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-5">
        <div>
          <h2 className="text-xl font-bold text-white">Trip Summary</h2>
          <p className="text-sm text-slate-400 mt-1">
            {driverInfo.driver_name} • {driverInfo.carrier_name} • {driverInfo.truck_number}
          </p>
        </div>
        <div className="px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
          HOS Compliant
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="bg-slate-800/50 rounded-xl p-4 text-center">
            <div className="text-2xl mb-1">{s.icon}</div>
            <div className="text-white font-bold text-lg">{s.value}</div>
            <div className="text-slate-500 text-xs mt-1">{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
