import axios from 'axios'
import { useMutation, useQuery } from '@tanstack/react-query'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

/* ─── Types ─── */

export interface TripPlanRequest {
  current_location: string
  pickup_location: string
  dropoff_location: string
  cycle_used_hours: number
  trip_start?: string
}

export interface Segment {
  status: 'OFF_DUTY' | 'SLEEPER_BERTH' | 'DRIVING' | 'ON_DUTY_NOT_DRIVING'
  start: number
  end: number
  location: string
  activity: string | null
  stationary: boolean
}

export interface LogSheet {
  day_index: number
  date: string
  total_miles_today: number
  segments: Segment[]
  totals: {
    off_duty: number
    sleeper_berth: number
    driving: number
    on_duty_not_driving: number
    combined_driving_and_on_duty: number
  }
  recap: {
    cycle_hours_used_today: number
  }
}

export interface Stop {
  type: string
  label: string
  lat: number
  lng: number
}

export interface TripPlanResponse {
  trip_id: string
  driver_info: {
    driver_name: string
    driver_id: string
    carrier_name: string
    main_office_address: string
    truck_number: string
    trailer_number: string
  }
  summary: {
    total_distance_miles: number
    total_driving_hours: number
    total_trip_duration_hours: number
    num_log_sheets: number
  }
  route: {
    geometry: {
      type: string
      coordinates: number[][]
    }
    stops: Stop[]
  }
  log_sheets: LogSheet[]
}

/* ─── Hooks ─── */

export function usePlanTrip() {
  return useMutation({
    mutationFn: async (data: TripPlanRequest): Promise<TripPlanResponse> => {
      const res = await api.post('/api/trips/plan', data)
      return res.data
    },
  })
}

export function useFetchTrip(tripId: string | undefined) {
  return useQuery<TripPlanResponse>({
    queryKey: ['trip', tripId],
    queryFn: async () => {
      const res = await api.get(`/api/trips/${tripId}`)
      return res.data
    },
    enabled: !!tripId,
  })
}
