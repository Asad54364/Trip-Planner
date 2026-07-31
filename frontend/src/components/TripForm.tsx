import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePlanTrip } from '../api/client'

export default function TripForm() {
  const navigate = useNavigate()
  const planTrip = usePlanTrip()

  const [form, setForm] = useState({
    current_location: '',
    pickup_location: '',
    dropoff_location: '',
    cycle_used_hours: '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  function validate(): boolean {
    const e: Record<string, string> = {}
    if (!form.current_location.trim()) e.current_location = 'Required'
    if (!form.pickup_location.trim()) e.pickup_location = 'Required'
    if (!form.dropoff_location.trim()) e.dropoff_location = 'Required'
    const hrs = parseFloat(form.cycle_used_hours)
    if (isNaN(hrs) || hrs < 0 || hrs > 70) {
      e.cycle_used_hours = 'Must be 0–70'
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return

    planTrip.mutate(
      {
        current_location: form.current_location.trim(),
        pickup_location: form.pickup_location.trim(),
        dropoff_location: form.dropoff_location.trim(),
        cycle_used_hours: parseFloat(form.cycle_used_hours),
      },
      {
        onSuccess: (data) => {
          navigate(`/trips/${data.trip_id}`)
        },
      },
    )
  }

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: '' }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Current Location */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          📍 Current Location
        </label>
        <input
          id="current-location"
          type="text"
          className="input-field"
          placeholder="e.g. Dallas, TX"
          value={form.current_location}
          onChange={(e) => update('current_location', e.target.value)}
        />
        {errors.current_location && (
          <p className="text-red-400 text-xs mt-1">{errors.current_location}</p>
        )}
      </div>

      {/* Pickup Location */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          📦 Pickup Location
        </label>
        <input
          id="pickup-location"
          type="text"
          className="input-field"
          placeholder="e.g. Oklahoma City, OK"
          value={form.pickup_location}
          onChange={(e) => update('pickup_location', e.target.value)}
        />
        {errors.pickup_location && (
          <p className="text-red-400 text-xs mt-1">{errors.pickup_location}</p>
        )}
      </div>

      {/* Dropoff Location */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          🏁 Drop-off Location
        </label>
        <input
          id="dropoff-location"
          type="text"
          className="input-field"
          placeholder="e.g. Chicago, IL"
          value={form.dropoff_location}
          onChange={(e) => update('dropoff_location', e.target.value)}
        />
        {errors.dropoff_location && (
          <p className="text-red-400 text-xs mt-1">{errors.dropoff_location}</p>
        )}
      </div>

      {/* Cycle Used */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          ⏱️ Current Cycle Used (Hours)
          <span className="text-slate-500 font-normal ml-1">— 70-hr/8-day total</span>
        </label>
        <input
          id="cycle-used-hours"
          type="number"
          className="input-field"
          placeholder="e.g. 12.5"
          min="0"
          max="70"
          step="0.5"
          value={form.cycle_used_hours}
          onChange={(e) => update('cycle_used_hours', e.target.value)}
        />
        {errors.cycle_used_hours && (
          <p className="text-red-400 text-xs mt-1">{errors.cycle_used_hours}</p>
        )}
      </div>

      {/* Error message */}
      {planTrip.isError && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-300 text-sm">
          <p className="font-semibold">⚠ Error planning trip</p>
          <p className="mt-1 text-red-400/80">
            {(planTrip.error as Error)?.message || 'Something went wrong. Please try again.'}
          </p>
        </div>
      )}

      {/* Submit */}
      <button
        id="plan-trip-btn"
        type="submit"
        className="btn-primary w-full flex items-center justify-center gap-3"
        disabled={planTrip.isPending}
      >
        {planTrip.isPending ? (
          <>
            <span className="spinner" />
            Computing Route & HOS Schedule…
          </>
        ) : (
          <>
            🚛 Plan Trip & Generate Logs
          </>
        )}
      </button>
    </form>
  )
}
